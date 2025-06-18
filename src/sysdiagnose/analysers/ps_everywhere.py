#! /usr/bin/env python3

from typing import Generator, Set, Optional
from sysdiagnose.utils.base import BaseAnalyserInterface, logger
from sysdiagnose.parsers.ps import PsParser
from sysdiagnose.parsers.psthread import PsThreadParser
from sysdiagnose.parsers.spindumpnosymbols import SpindumpNoSymbolsParser
from sysdiagnose.parsers.shutdownlogs import ShutdownLogsParser
from sysdiagnose.parsers.logarchive import LogarchiveParser
from sysdiagnose.parsers.logdata_statistics import LogDataStatisticsParser
from sysdiagnose.parsers.logdata_statistics_txt import LogDataStatisticsTxtParser
from sysdiagnose.parsers.uuid2path import UUID2PathParser
from sysdiagnose.parsers.taskinfo import TaskinfoParser
from sysdiagnose.parsers.remotectl_dumpstate import RemotectlDumpstateParser


class PsEverywhereAnalyser(BaseAnalyserInterface):
    """
    Analyser that gathers process information from multiple sources
    to build a comprehensive list of running processes across different system logs.
    """

    description = "List all processes we can find a bit everywhere."
    format = "jsonl"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)
        self.all_ps: Set[str] = set()

    @staticmethod
    def _strip_flags(process: str) -> str:
        """
        Extracts the base command by removing everything after the first space.

        :param process: Full process command string.
        :return: Command string without flags.
        """
        process, *_ = process.partition(' ')
        return process

    @staticmethod
    def message_extract_binary(process: str, message: str) -> Optional[str | list[str]]:
        """
        Extracts process_name from special messages:
        1. backboardd Signpost messages with process_name
        2. tccd process messages with binary_path
        3. '/kernel' process messages with app name mapping format 'App Name -> /path/to/app'
        4. configd SCDynamicStore client sessions showing connected processes

        :param process: Process name.
        :param message: Log message potentially containing process information.
        :return: Extracted process name, list of process names, or None if not found.
        """
        # Case 1: Backboardd Signpost messages
        if process == '/usr/libexec/backboardd' and 'Signpost' in message and 'process_name=' in message:
            try:
                # Find the process_name part in the message
                process_name_start = message.find('process_name=')
                if process_name_start != -1:
                    # Extract from after 'process_name=' to the next space or end of string
                    process_name_start += len('process_name=')
                    process_name_end = message.find(' ', process_name_start)

                    if process_name_end == -1:  # If no space after process_name
                        return message[process_name_start:]
                    else:
                        return message[process_name_start:process_name_end]
            except Exception as e:
                logger.debug(f"Error extracting process_name from backboardd: {e}")

        # Case 2: TCCD process messages
        if process == '/System/Library/PrivateFrameworks/TCC.framework/Support/tccd' and 'binary_path=' in message:
            try:
                # Extract only the clean binary paths without additional context
                binary_paths = []

                # Find all occurrences of binary_path= in the message
                start_pos = 0
                while True:
                    binary_path_start = message.find('binary_path=', start_pos)
                    if binary_path_start == -1:
                        break

                    binary_path_start += len('binary_path=')
                    # Find the end of the path (comma, closing bracket, or end of string)
                    binary_path_end = None
                    for delimiter in [',', '}', ' access to', ' is checking']:
                        delimiter_pos = message.find(delimiter, binary_path_start)
                        if delimiter_pos != -1 and (binary_path_end is None or delimiter_pos < binary_path_end):
                            binary_path_end = delimiter_pos

                    if binary_path_end is None:
                        path = message[binary_path_start:].strip()
                    else:
                        path = message[binary_path_start:binary_path_end].strip()

                    # Skip paths with excessive information
                    if len(path) > 0 and path.startswith('/') and ' ' not in path:
                        binary_paths.append(path)

                    # Move to position after the current binary_path
                    start_pos = binary_path_start + 1

                # Return all valid binary paths
                if binary_paths:
                    logger.debug(f"Extracted {len(binary_paths)} binary paths from tccd message")
                    return binary_paths if len(binary_paths) > 1 else binary_paths[0]

            except Exception as e:
                logger.debug(f"Error extracting binary_path from tccd: {e}")

        # Case 3: /kernel process with App name mapping pattern "App Name -> /path/to/app"
        if process == '/kernel' and ' -> ' in message and 'App Store Fast Path' in message:
            try:
                # Find the arrow mapping pattern
                arrow_pos = message.find(' -> ')
                if arrow_pos != -1:
                    path_start = arrow_pos + len(' -> ')
                    # Look for common path patterns - more flexible for kernel messages
                    if message[path_start:].startswith('/'):
                        # Find the end of the path (space or end of string)
                        path_end = message.find(' ', path_start)
                        if path_end == -1:  # If no space after path
                            return message[path_start:]
                        else:
                            return message[path_start:path_end]
            except Exception as e:
                logger.debug(f"Error extracting app path from kernel mapping: {e}")

        # Case 4: configd SCDynamicStore client sessions
        if process == '/usr/libexec/configd' and 'SCDynamicStore/client sessions' in message:
            try:
                # Process the list of connected clients from configd
                process_paths = []
                lines = message.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('"') and '=' in line:
                        # Extract the client path from lines like ""/usr/sbin/mDNSResponder:null" = 1;"
                        client_path = line.split('"')[1]  # Get the part between the first pair of quotes
                        if ':' in client_path:
                            # Extract the actual process path part (before the colon)
                            process_path = client_path.split(':')[0]
                            if process_path.startswith('/') or process_path.startswith('com.apple.'):
                                process_paths.append(process_path)

                # Return the list of process paths if any were found
                if process_paths:
                    logger.debug(f"Extracted {len(process_paths)} process paths from configd message")
                    return process_paths
            except Exception as e:
                logger.debug(f"Error extracting client paths from configd SCDynamicStore: {e}")

        return None

    def execute(self) -> Generator[dict, None, None]:
        """
        Executes all extraction methods dynamically, ensuring that each extracted process is unique.

        :yield: A dictionary containing process details from various sources.
        """
        for func in dir(self):
            if func.startswith(f"_{self.__class__.__name__}__extract_ps_"):
                yield from getattr(self, func)()  # Dynamically call extract methods

    def __extract_ps_base_file(self) -> Generator[dict, None, None]:
        """
        Extracts process data from ps.txt.

        :return: A generator yielding dictionaries containing process details from ps.txt.
        """
        entity_type = 'ps.txt'
        try:
            for p in PsParser(self.config, self.case_id).get_result():
                ps_event = {
                    'process': self._strip_flags(p['command']),
                    'timestamp': p['timestamp'],
                    'datetime': p['datetime'],
                    'source': entity_type
                }
                if self.add_if_full_command_is_not_in_set(ps_event['process']):
                    yield ps_event
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type} file. {e}")

    def __extract_ps_thread_file(self) -> Generator[dict, None, None]:
        """
        Extracts process data from psthread.txt.

        :return: A generator yielding dictionaries containing process details from psthread.txt.
        """
        entity_type = 'psthread.txt'
        try:
            for p in PsThreadParser(self.config, self.case_id).get_result():
                ps_event = {
                    'process': self._strip_flags(p['command']),
                    'timestamp': p['timestamp'],
                    'datetime': p['datetime'],
                    'source': entity_type
                }
                if self.add_if_full_command_is_not_in_set(ps_event['process']):
                    yield ps_event
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type} file. {e}")

    def __extract_ps_spindump_nosymbols_file(self) -> Generator[dict, None, None]:
        """
        Extracts process data from spindump-nosymbols.txt.

        :return: A generator yielding dictionaries containing process and thread details from spindump-nosymbols.txt.
        """
        entity_type = 'spindump-nosymbols.txt'
        try:
            for p in SpindumpNoSymbolsParser(self.config, self.case_id).get_result():
                if 'process' not in p:
                    continue
                process_name = p.get('path', '/kernel' if p['process'] == 'kernel_task [0]' else p['process'])

                if self.add_if_full_command_is_not_in_set(self._strip_flags(process_name)):
                    yield {
                        'process': self._strip_flags(process_name),
                        'timestamp': p['timestamp'],
                        'datetime': p['datetime'],
                        'source': entity_type
                    }

                for t in p['threads']:
                    try:
                        thread_name = f"{self._strip_flags(process_name)}::{t['thread_name']}"
                        if self.add_if_full_command_is_not_in_set(thread_name):
                            yield {
                                'process': thread_name,
                                'timestamp': p['timestamp'],
                                'datetime': p['datetime'],
                                'source': entity_type
                            }
                    except KeyError:
                        pass
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type} file. {e}")

    def __extract_ps_shutdownlogs(self) -> Generator[dict, None, None]:
        """
        Extracts process data from shutdown logs.

        :return: A generator yielding dictionaries containing process details from shutdown logs.
        """
        entity_type = 'shutdown.logs'
        try:
            for p in ShutdownLogsParser(self.config, self.case_id).get_result():
                if self.add_if_full_command_is_not_in_set(self._strip_flags(p['command'])):
                    yield {
                        'process': self._strip_flags(p['command']),
                        'timestamp': p['timestamp'],
                        'datetime': p['datetime'],
                        'source': entity_type
                    }
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type}. {e}")

    def __extract_ps_logarchive(self) -> Generator[dict, None, None]:
        """
        Extracts process data from logarchive.

        :return: A generator yielding dictionaries containing process details from logarchive.
        """
        entity_type = 'log archive'
        try:
            for p in LogarchiveParser(self.config, self.case_id).get_result():
                # First check if we can extract a binary from the message
                if 'message' in p:
                    extracted_process = self.message_extract_binary(p['process'], p['message'])
                    if extracted_process:
                        # Handle the case where extracted_process is a list of paths
                        if isinstance(extracted_process, list):
                            for proc_path in extracted_process:
                                if self.add_if_full_command_is_not_in_set(self._strip_flags(proc_path)):
                                    yield {
                                        'process': self._strip_flags(proc_path),
                                        'timestamp': p['timestamp'],
                                        'datetime': p['datetime'],
                                        'source': entity_type
                                    }
                        else:
                            # Handle the case where it's a single string
                            if self.add_if_full_command_is_not_in_set(self._strip_flags(extracted_process)):
                                yield {
                                    'process': self._strip_flags(extracted_process),
                                    'timestamp': p['timestamp'],
                                    'datetime': p['datetime'],
                                    'source': entity_type
                                }

                # Process the original process name
                if self.add_if_full_command_is_not_in_set(self._strip_flags(p['process'])):
                    yield {
                        'process': self._strip_flags(p['process']),
                        'timestamp': p['timestamp'],
                        'datetime': p['datetime'],
                        'source': entity_type
                    }
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type}. {e}")

    def __extract_ps_uuid2path(self) -> Generator[dict, None, None]:
        """
        Extracts process data from UUID2PathParser.

        :return: A generator yielding process data from uuid2path.
        """
        entity_type = 'uuid2path'
        try:
            for p in UUID2PathParser(self.config, self.case_id).get_result().values():
                if self.add_if_full_command_is_not_in_set(self._strip_flags(p)):
                    yield {
                        'process': self._strip_flags(p),
                        'timestamp': None,
                        'datetime': None,
                        'source': entity_type
                    }
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type}. {e}")

    def __extract_ps_taskinfo(self) -> Generator[dict, None, None]:
        """
        Extracts process and thread information from TaskinfoParser.

        :return: A generator yielding process and thread information from taskinfo.
        """
        entity_type = 'taskinfo.txt'
        try:
            for p in TaskinfoParser(self.config, self.case_id).get_result():
                if 'name' not in p:
                    continue

                if self.add_if_full_path_is_not_in_set(self._strip_flags(p['name'])):
                    yield {
                        'process': self._strip_flags(p['name']),
                        'timestamp': p['timestamp'],
                        'datetime': p['datetime'],
                        'source': entity_type
                    }

                for t in p['threads']:
                    try:
                        thread_name = f"{self._strip_flags(p['name'])}::{t['thread name']}"
                        if self.add_if_full_path_is_not_in_set(thread_name):
                            yield {
                                'process': thread_name,
                                'timestamp': p['timestamp'],
                                'datetime': p['datetime'],
                                'source': entity_type
                            }
                    except KeyError:
                        pass
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type}. {e}")

    def __extract_ps_remotectl_dumpstate(self) -> Generator[dict, None, None]:
        """
        Extracts process data from RemotectlDumpstateParser.

        :return: A generator yielding process data from remotectl_dumpstate.txt.
        """
        entity_type = 'remotectl_dumpstate.txt'
        try:
            remotectl_dumpstate_json = RemotectlDumpstateParser(self.config, self.case_id).get_result()
            if remotectl_dumpstate_json:
                for p in remotectl_dumpstate_json['Local device']['Services']:
                    if self.add_if_full_path_is_not_in_set(self._strip_flags(p)):
                        yield {
                            'process': self._strip_flags(p),
                            'timestamp': None,
                            'datetime': None,
                            'source': entity_type
                        }
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type}. {e}")

    def __extract_ps_logdata_statistics(self) -> Generator[dict, None, None]:
        """
        Extracts process data from logdata_statistics.jsonl.

        :return: A generator yielding process data from logdata_statistics.jsonl.
        """
        entity_type = 'logdata.statistics.jsonl'
        try:
            for p in LogDataStatisticsParser(self.config, self.case_id).get_result():
                if self.add_if_full_command_is_not_in_set(self._strip_flags(p['process'])):
                    yield {
                        'process': self._strip_flags(p['process']),
                        'timestamp': p['timestamp'],
                        'datetime': p['datetime'],
                        'source': entity_type
                    }
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type}. {e}")

    def __extract_ps_logdata_statistics_txt(self) -> Generator[dict, None, None]:
        """
        Extracts process data from logdata.statistics.txt.

        :return: A generator yielding process data from logdata.statistics.txt.
        """
        entity_type = "logdata.statistics.txt"

        try:
            for p in LogDataStatisticsTxtParser(self.config, self.case_id).get_result():
                if self.add_if_full_path_is_not_in_set(self._strip_flags(p['process'])):
                    yield {
                        'process': self._strip_flags(p['process']),
                        'timestamp': p['timestamp'],
                        'datetime': p['datetime'],
                        'source': entity_type
                    }
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type}. {e}")

    def add_if_full_path_is_not_in_set(self, name: str) -> bool:
        """
        Ensures that a process path is unique before adding it to the shared set.

        :param name: Process path name
        :return: True if the process was not in the set and was added, False otherwise.
        """
        for item in self.all_ps:
            if item.endswith(name):
                return False
            if item.split('::')[0].endswith(name):
                return False
            if '::' not in item and item.split(' ')[0].endswith(name):
                return False  # This covers cases with space-separated commands
        self.all_ps.add(name)
        return True

    def add_if_full_command_is_not_in_set(self, name: str) -> bool:
        """
        Ensures that a process command is unique before adding it to the shared set.

        :param name: Process command name
        :return: True if the process was not in the set and was added, False otherwise.
        """
        for item in self.all_ps:
            if item.startswith(name):
                return False
        self.all_ps.add(name)
        return True
