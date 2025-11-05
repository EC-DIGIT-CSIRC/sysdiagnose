#! /usr/bin/env python3

from datetime import datetime, timedelta
from typing import Generator, Set, Optional, Dict
from sysdiagnose.parsers import ps
from sysdiagnose.utils.base import BaseAnalyserInterface, SysdiagnoseConfig, logger, Event
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

    The timestamp is 'a' time the process was seen in the log, without being specifically the first or last seen.

    Deduplication strategy: Processes are deduplicated within a 1-hour window. If the same process
    appears more than 1 hour apart, both occurrences are kept to track temporal patterns.
    """

    description = "List all processes we can find a bit everywhere."
    format = "jsonl"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)
        self.all_ps: Set[str] = set()
        # Track last seen timestamp for each process (for time-based deduplication)
        self.process_last_seen: Dict[str, datetime] = {}

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
    def _sanitize_uid(uid: Optional[int]) -> Optional[int]:
        """
        Sanitizes UID values by filtering out invalid/placeholder values.

        :param uid: The UID value to sanitize
        :return: The UID if valid, None if invalid/placeholder
        """
        # 0xAAAAAAAA (2863311530) is a common placeholder/uninitialized value
        # 0xFFFFFFFF (4294967295) is -1 as unsigned, also invalid
        if uid in (2863311530, 4294967295):
            return None
        return uid

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
                uid = self._sanitize_uid(p['data'].get('uid'))
                ps_event = Event(
                    datetime=datetime.fromisoformat(p['datetime']),
                    message= self._strip_flags(p['data']['command']),
                    timestamp_desc=p['timestamp_desc'],
                    module=self.module_name,
                    data={'source': entity_type, 'uid': uid}
                )
                if self.add_if_full_command_is_not_in_set(ps_event.message, ps_event.datetime, uid):
                    yield ps_event.to_dict()
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
                uid = self._sanitize_uid(p['data'].get('uid'))
                ps_event = Event(
                    datetime=datetime.fromisoformat(p['datetime']),
                    message=self._strip_flags(p['data']['command']),
                    timestamp_desc=p['timestamp_desc'],
                    module=self.module_name,
                    data={'source': entity_type, 'uid': uid}
                )
                if self.add_if_full_command_is_not_in_set(ps_event.message, ps_event.datetime, uid):
                    yield ps_event.to_dict()
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type} file. {e}")

    def __extract_ps_spindump_nosymbols_file(self) -> Generator[dict, None, None]:
        """
        Extracts process data from spindump-nosymbols.txt.

        :return: A generator yielding dictionaries containing process and thread details from spindump-nosymbols.txt.
        """
        entity_type = 'spindump-nosymbols.txt'
        try:
            for event in SpindumpNoSymbolsParser(self.config, self.case_id).get_result():
                p = event['data']
                if 'process' not in p:
                    continue
                process_name = p.get('path', '/kernel' if p['process'] == 'kernel_task [0]' else p['process'])
                event_datetime = datetime.fromisoformat(event['datetime'])
                uid = self._sanitize_uid(p.get('uid'))

                if self.add_if_full_command_is_not_in_set(self._strip_flags(process_name), event_datetime, uid):
                    yield Event(
                        datetime=event_datetime,
                        message=self._strip_flags(process_name),
                        timestamp_desc=event['timestamp_desc'],
                        module=self.module_name,
                        data={'source': entity_type, 'uid': uid}
                    ).to_dict()

                for t in p['threads']:
                    try:
                        thread_name = f"{self._strip_flags(process_name)}::{t['thread_name']}"
                        if self.add_if_full_command_is_not_in_set(thread_name, event_datetime, uid):
                            yield Event(
                                datetime=event_datetime,
                                message=self._strip_flags(thread_name),
                                timestamp_desc=event['timestamp_desc'],
                                module=self.module_name,
                                data={'source': entity_type, 'uid': uid}
                            ).to_dict()
                    except KeyError:
                        pass
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type} file. {e}")

    def __extract_ps_shutdownlogs(self) -> Generator[dict, None, None]:
        """
        Extracts process data from shutdown logs.

        Note: Unlike other sources, shutdown logs always keep all entries even if duplicate,
        as each entry represents a different shutdown event where the process was blocking.

        :return: A generator yielding dictionaries containing process details from shutdown logs.
        """
        entity_type = 'shutdown.logs'
        try:
            for p in ShutdownLogsParser(self.config, self.case_id).get_result():
                # Always yield shutdown log entries, even if duplicate
                # Each occurrence represents a different shutdown event
                yield Event(
                    datetime=datetime.fromisoformat(p['datetime']),
                    message=self._strip_flags(p['data']['command']),
                    timestamp_desc=p['timestamp_desc'],
                    module=self.module_name,
                    data={'source': entity_type, 'uid': None}
                ).to_dict()
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
                p_datetime = datetime.fromisoformat(p['datetime'])
                euid = self._sanitize_uid(p['data'].get('euid'))

                # First check if we can extract a binary from the message
                extracted_process = self.message_extract_binary(p['data']['process'], p['message'])
                if extracted_process:
                    # Handle the case where extracted_process is a list of paths
                    if isinstance(extracted_process, list):
                        for proc_path in extracted_process:
                            if self.add_if_full_command_is_not_in_set(self._strip_flags(proc_path), p_datetime, None):
                                yield Event(
                                    p_datetime,
                                    message=self._strip_flags(proc_path),
                                    timestamp_desc=p['timestamp_desc'],
                                    module=self.module_name,
                                    data={'source': entity_type, 'uid': None}
                                ).to_dict()
                    else:
                        # Handle the case where it's a single string
                        if self.add_if_full_command_is_not_in_set(self._strip_flags(extracted_process), p_datetime, None):
                            yield Event(
                                datetime=p_datetime,
                                message=self._strip_flags(extracted_process),
                                timestamp_desc=p['timestamp_desc'],
                                module=self.module_name,
                                data={'source': entity_type, 'uid': None}
                            ).to_dict()

                # Process the original process name
                if self.add_if_full_command_is_not_in_set(self._strip_flags(p['data']['process']), p_datetime, euid):
                    yield Event(
                        datetime=p_datetime,
                        message=self._strip_flags(p['data']['process']),
                        timestamp_desc=p['timestamp_desc'],
                        module=self.module_name,
                        data={'source': entity_type, 'uid': euid}
                    ).to_dict()
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
                if self.add_if_full_command_is_not_in_set(self._strip_flags(p), self.sysdiagnose_creation_datetime, None):
                    yield Event(
                        datetime=self.sysdiagnose_creation_datetime,
                        message=self._strip_flags(p),
                        timestamp_desc="Process path from UUID existing at sysdiagnose creation time",
                        module=self.module_name,
                        data={'source': entity_type, 'uid': None}
                    ).to_dict()
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
                if 'name' not in p['data']:
                    continue

                p_datetime = datetime.fromisoformat(p['datetime'])
                if self.add_if_full_path_is_not_in_set(self._strip_flags(p['data']['name']), p_datetime, None):
                    yield Event(
                        datetime=p_datetime,
                        message=self._strip_flags(p['data']['name']),
                        timestamp_desc=p['timestamp_desc'],
                        module=self.module_name,
                        data={'source': entity_type, 'uid': None}
                    ).to_dict()

                for t in p['data']['threads']:
                    try:
                        thread_name = f"{self._strip_flags(p['data']['name'])}::{t['thread name']}"
                        if self.add_if_full_path_is_not_in_set(thread_name, p_datetime, None):
                            yield Event(
                                p_datetime,
                                message=thread_name,
                                timestamp_desc=p['timestamp_desc'],
                                module=self.module_name,
                                data={'source': entity_type, 'uid': None}
                            ).to_dict()
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
                    if self.add_if_full_path_is_not_in_set(self._strip_flags(p), self.sysdiagnose_creation_datetime, None):
                        yield Event(
                            datetime=self.sysdiagnose_creation_datetime,
                            message=self._strip_flags(p),
                            timestamp_desc="Existing service at sysdiagnose creation time",
                            module=self.module_name,
                            data={'source': entity_type, 'uid': None}
                        ).to_dict()
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
                p_datetime = datetime.fromisoformat(p['datetime'])
                if self.add_if_full_command_is_not_in_set(self._strip_flags(p['data']['process']), p_datetime, None):
                    yield Event(
                        datetime=p_datetime,
                        message=self._strip_flags(p['data']['process']),
                        timestamp_desc=p['timestamp_desc'],
                        module=self.module_name,
                        data={'source': entity_type, 'uid': None}
                    ).to_dict()
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
                p_datetime = datetime.fromisoformat(p['datetime'])
                if self.add_if_full_path_is_not_in_set(self._strip_flags(p['data']['process']), p_datetime, None):
                    yield Event(
                        datetime=p_datetime,
                        message=self._strip_flags(p['data']['process']),
                        timestamp_desc=p['timestamp_desc'],
                        module=self.module_name,
                        data={'source': entity_type, 'uid': None}
                    ).to_dict()

        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type}. {e}")

    def add_if_full_path_is_not_in_set(self, name: str, timestamp: Optional[datetime] = None, uid: Optional[int] = None) -> bool:
        """
        Ensures that a process path is unique before adding it to the shared set,
        with time-based deduplication: only keep duplicates if they occur more than 1 hour apart.
        UID is considered part of the uniqueness - same process with different UID is treated as separate.

        :param name: Process path name
        :param timestamp: Timestamp of the process occurrence (optional, for time-based deduplication)
        :param uid: User ID of the process (optional, considered in uniqueness check)
        :return: True if the process was not in the set or last seen > 1 hour ago, False otherwise.
        """
        # Create a unique key that includes both name and UID
        unique_key = f"{name}|uid:{uid}"

        # If no timestamp provided, use old behavior (always check for duplicates)
        if timestamp is None:
            for item in self.all_ps:
                if item.endswith(name):
                    return False
                if item.split('::')[0].endswith(name):
                    return False
                if '::' not in item and item.split(' ')[0].endswith(name):
                    return False  # This covers cases with space-separated commands
            self.all_ps.add(unique_key)
            return True

        # Time-based deduplication: check if we've seen this process+uid combination recently
        if unique_key in self.process_last_seen:
            time_diff = timestamp - self.process_last_seen[unique_key]
            # Only add if more than 1 hour has passed
            if time_diff < timedelta(hours=1):
                return False

        # Add or update the process
        self.all_ps.add(unique_key)
        self.process_last_seen[unique_key] = timestamp
        return True

    def add_if_full_command_is_not_in_set(self, name: str, timestamp: Optional[datetime] = None, uid: Optional[int] = None) -> bool:
        """
        Ensures that a process command is unique before adding it to the shared set,
        with time-based deduplication: only keep duplicates if they occur more than 1 hour apart.
        UID is considered part of the uniqueness - same process with different UID is treated as separate.

        :param name: Process command name
        :param timestamp: Timestamp of the process occurrence (optional, for time-based deduplication)
        :param uid: User ID of the process (optional, considered in uniqueness check)
        :return: True if the process was not in the set or last seen > 1 hour ago, False otherwise.
        """
        # Create a unique key that includes both name and UID
        unique_key = f"{name}|uid:{uid}"

        # If no timestamp provided, use old behavior (always check for duplicates)
        if timestamp is None:
            for item in self.all_ps:
                if item.startswith(name):
                    return False
            self.all_ps.add(unique_key)
            return True

        # Time-based deduplication: check if we've seen this process+uid combination recently
        if unique_key in self.process_last_seen:
            time_diff = timestamp - self.process_last_seen[unique_key]
            # Only add if more than 1 hour has passed
            if time_diff < timedelta(hours=1):
                return False

        # Add or update the process
        self.all_ps.add(unique_key)
        self.process_last_seen[unique_key] = timestamp
        return True
