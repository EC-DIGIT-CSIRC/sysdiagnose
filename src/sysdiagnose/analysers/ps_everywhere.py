#! /usr/bin/env python3

from datetime import datetime
from typing import Generator, Set, Optional, Tuple
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
    This version includes UID tracking for better process uniqueness detection.
    """

    description = "List all processes we can find a bit everywhere."
    format = "jsonl"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)
        self.all_ps: Set[Tuple[str, Optional[int]]] = set()  # Stores tuples of (process, uid/euid)

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
    def extract_euid_from_tccd_message(message: str, binary_path: str) -> Optional[int]:
        """
        Extracts the euid for a specific binary_path from a tccd message.
        
        :param message: Log message containing process information with euid
        :param binary_path: The specific binary path to extract euid for
        :return: The euid as an integer, or None if not found
        """
        try:
            # Look for pattern: euid=XXX before binary_path=/path/to/binary
            search_pattern = f'binary_path={binary_path}'
            start_pos = message.find(search_pattern)
            if start_pos == -1:
                return None
            
            # Get the substring before binary_path and find the last euid=
            before_binary = message[:start_pos]
            euid_pos = before_binary.rfind('euid=')
            if euid_pos == -1:
                return None
            
            # Extract the euid value
            euid_start = euid_pos + len('euid=')
            euid_end = message.find(',', euid_start)
            if euid_end == -1:
                euid_end = message.find(' ', euid_start)
            if euid_end == -1:
                euid_end = message.find('}', euid_start)
            
            euid_str = message[euid_start:euid_end].strip() if euid_end != -1 else message[euid_start:].strip()
            return int(euid_str)
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error extracting euid for binary {binary_path}: {e}")
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
        """
        entity_type = 'ps.txt'
        try:
            for p in PsParser(self.config, self.case_id).get_result():
                uid = p['data'].get('uid')
                process_name = self._strip_flags(p['data']['command'])
                
                if self.add_if_full_command_is_not_in_set(process_name, uid):
                    yield Event(
                        datetime=datetime.fromisoformat(p['datetime']),
                        message=process_name,
                        timestamp_desc=p['timestamp_desc'],
                        module=self.module_name,
                        data={'source': entity_type, 'uid': uid}
                    ).to_dict()
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type} file. {e}")

    def __extract_ps_thread_file(self) -> Generator[dict, None, None]:
        """
        Extracts process data from psthread.txt.
        """
        entity_type = 'psthread.txt'
        try:
            for p in PsThreadParser(self.config, self.case_id).get_result():
                uid = p['data'].get('uid')
                process_name = self._strip_flags(p['data']['command'])
                
                if self.add_if_full_command_is_not_in_set(process_name, uid):
                    yield Event(
                        datetime=datetime.fromisoformat(p['datetime']),
                        message=process_name,
                        timestamp_desc=p['timestamp_desc'],
                        module=self.module_name,
                        data={'source': entity_type, 'uid': uid}
                    ).to_dict()
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type} file. {e}")

    def __extract_ps_spindump_nosymbols_file(self) -> Generator[dict, None, None]:
        """
        Extracts process data from spindump-nosymbols.txt.
        """
        entity_type = 'spindump-nosymbols.txt'
        try:
            for event_data in SpindumpNoSymbolsParser(self.config, self.case_id).get_result():
                p = event_data['data']
                if 'process' not in p:
                    continue
                
                process_name = p.get('path', '/kernel' if p['process'] == 'kernel_task [0]' else p['process'])
                uid = p.get('uid')
                
                if self.add_if_full_command_is_not_in_set(self._strip_flags(process_name), uid):
                    yield Event(
                        datetime=datetime.fromisoformat(event_data['datetime']),
                        message=self._strip_flags(process_name),
                        timestamp_desc=event_data['timestamp_desc'],
                        module=self.module_name,
                        data={'source': entity_type, 'uid': uid}
                    ).to_dict()

                # Process threads
                for t in p.get('threads', []):
                    try:
                        thread_name = f"{self._strip_flags(process_name)}::{t['thread_name']}"
                        if self.add_if_full_command_is_not_in_set(thread_name, uid):
                            yield Event(
                                datetime=datetime.fromisoformat(event_data['datetime']),
                                message=thread_name,
                                timestamp_desc=event_data['timestamp_desc'],
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
        """
        entity_type = 'shutdown.logs'
        try:
            for p in ShutdownLogsParser(self.config, self.case_id).get_result():
                uid = p['data'].get('uid')
                auid = p['data'].get('auid')
                process_name = self._strip_flags(p['data']['command'])
                
                # Use uid for uniqueness check, fallback to auid
                uniqueness_uid = uid if uid is not None else auid
                
                if self.add_if_full_command_is_not_in_set(process_name, uniqueness_uid):
                    yield Event(
                        datetime=datetime.fromisoformat(p['datetime']),
                        message=process_name,
                        timestamp_desc=p['timestamp_desc'],
                        module=self.module_name,
                        data={'source': entity_type, 'uid': uid, 'auid': auid}
                    ).to_dict()
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type}. {e}")

    def __extract_ps_logarchive(self) -> Generator[dict, None, None]:
        """
        Extracts process data from logarchive.
        """
        entity_type = 'log archive'
        try:
            for p in LogarchiveParser(self.config, self.case_id).get_result():
                # First check for special message patterns that contain process information
                if 'message' in p:
                    extracted_processes = self._extract_processes_from_message(
                        p['data'].get('process', ''), 
                        p['message']
                    )
                    for proc_info in extracted_processes:
                        process_path = proc_info['path']
                        euid = proc_info.get('euid', p['data'].get('euid'))
                        
                        if self.add_if_full_command_is_not_in_set(self._strip_flags(process_path), euid):
                            yield Event(
                                datetime=datetime.fromisoformat(p['datetime']),
                                message=self._strip_flags(process_path),
                                timestamp_desc=p['timestamp_desc'],
                                module=self.module_name,
                                data={'source': entity_type + ' message', 'uid': euid}
                            ).to_dict()

                # Process the original process name
                euid = p['data'].get('euid')
                process_name = self._strip_flags(p['data']['process'])
                
                if self.add_if_full_command_is_not_in_set(process_name, euid):
                    yield Event(
                        datetime=datetime.fromisoformat(p['datetime']),
                        message=process_name,
                        timestamp_desc=p['timestamp_desc'],
                        module=self.module_name,
                        data={'source': entity_type, 'uid': euid}
                    ).to_dict()
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type}. {e}")

    def _extract_processes_from_message(self, process: str, message: str) -> list[dict]:
        """
        Extracts process information from special log messages.
        Returns a list of dicts with 'path' and optionally 'euid' keys.
        """
        processes = []
        
        # Case 1: Backboardd Signpost messages
        if process == '/usr/libexec/backboardd' and 'Signpost' in message and 'process_name=' in message:
            try:
                process_name_start = message.find('process_name=')
                if process_name_start != -1:
                    process_name_start += len('process_name=')
                    process_name_end = message.find(' ', process_name_start)
                    path = message[process_name_start:process_name_end] if process_name_end != -1 else message[process_name_start:]
                    processes.append({'path': path})
            except Exception as e:
                logger.debug(f"Error extracting process_name from backboardd: {e}")

        # Case 2: TCCD process messages with binary_path and euid
        elif process == '/System/Library/PrivateFrameworks/TCC.framework/Support/tccd' and 'binary_path=' in message:
            try:
                start_pos = 0
                while True:
                    binary_path_start = message.find('binary_path=', start_pos)
                    if binary_path_start == -1:
                        break
                    
                    binary_path_start += len('binary_path=')
                    binary_path_end = None
                    for delimiter in [',', '}', ' access to', ' is checking']:
                        delimiter_pos = message.find(delimiter, binary_path_start)
                        if delimiter_pos != -1 and (binary_path_end is None or delimiter_pos < binary_path_end):
                            binary_path_end = delimiter_pos
                    
                    path = message[binary_path_start:binary_path_end].strip() if binary_path_end else message[binary_path_start:].strip()
                    
                    if path and path.startswith('/') and ' ' not in path:
                        proc_info = {'path': path}
                        # Try to extract euid for this specific binary
                        euid = self.extract_euid_from_tccd_message(message, path)
                        if euid is not None:
                            proc_info['euid'] = euid
                        processes.append(proc_info)
                    
                    start_pos = binary_path_start + 1
            except Exception as e:
                logger.debug(f"Error extracting binary_path from tccd: {e}")

        # Case 3: /kernel process with App name mapping
        elif process == '/kernel' and ' -> ' in message and 'App Store Fast Path' in message:
            try:
                arrow_pos = message.find(' -> ')
                if arrow_pos != -1:
                    path_start = arrow_pos + len(' -> ')
                    if message[path_start:].startswith('/'):
                        path_end = message.find(' ', path_start)
                        path = message[path_start:path_end] if path_end != -1 else message[path_start:]
                        processes.append({'path': path})
            except Exception as e:
                logger.debug(f"Error extracting app path from kernel mapping: {e}")

        # Case 4: configd SCDynamicStore client sessions
        elif process == '/usr/libexec/configd' and 'SCDynamicStore/client sessions' in message:
            try:
                lines = message.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('"') and '=' in line:
                        client_path = line.split('"')[1]
                        if ':' in client_path:
                            process_path = client_path.split(':')[0]
                            if process_path.startswith('/') or process_path.startswith('com.apple.'):
                                processes.append({'path': process_path})
            except Exception as e:
                logger.debug(f"Error extracting client paths from configd: {e}")

        return processes

    def __extract_ps_uuid2path(self) -> Generator[dict, None, None]:
        """
        Extracts process data from UUID2PathParser.
        """
        entity_type = 'uuid2path'
        try:
            for p in UUID2PathParser(self.config, self.case_id).get_result().values():
                if self.add_if_full_command_is_not_in_set(self._strip_flags(p), None):
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
        """
        entity_type = 'taskinfo.txt'
        try:
            for p in TaskinfoParser(self.config, self.case_id).get_result():
                if 'name' not in p['data']:
                    continue

                uid = p['data'].get('uid')
                auid = p['data'].get('auid')
                process_name = self._strip_flags(p['data']['name'])
                
                # Use uid for uniqueness check, fallback to auid
                uniqueness_uid = uid if uid is not None else auid
                
                if self.add_if_full_path_is_not_in_set(process_name, uniqueness_uid):
                    yield Event(
                        datetime=datetime.fromisoformat(p['datetime']),
                        message=process_name,
                        timestamp_desc=p['timestamp_desc'],
                        module=self.module_name,
                        data={'source': entity_type, 'uid': uid, 'auid': auid}
                    ).to_dict()

                # Process threads
                for t in p['data'].get('threads', []):
                    try:
                        thread_name = f"{process_name}::{t['thread name']}"
                        if self.add_if_full_path_is_not_in_set(thread_name, uniqueness_uid):
                            yield Event(
                                datetime=datetime.fromisoformat(p['datetime']),
                                message=thread_name,
                                timestamp_desc=p['timestamp_desc'],
                                module=self.module_name,
                                data={'source': entity_type, 'uid': uid, 'auid': auid}
                            ).to_dict()
                    except KeyError:
                        pass
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type}. {e}")

    def __extract_ps_remotectl_dumpstate(self) -> Generator[dict, None, None]:
        """
        Extracts process data from RemotectlDumpstateParser.
        """
        entity_type = 'remotectl_dumpstate.txt'
        try:
            remotectl_dumpstate_json = RemotectlDumpstateParser(self.config, self.case_id).get_result()
            if remotectl_dumpstate_json:
                for p in remotectl_dumpstate_json['Local device']['Services']:
                    if self.add_if_full_path_is_not_in_set(self._strip_flags(p), None):
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
        """
        entity_type = 'logdata.statistics.jsonl'
        try:
            for p in LogDataStatisticsParser(self.config, self.case_id).get_result():
                uid = p['data'].get('uid', p['data'].get('euid'))
                process_name = self._strip_flags(p['data']['process'])
                
                if self.add_if_full_command_is_not_in_set(process_name, uid):
                    yield Event(
                        datetime=datetime.fromisoformat(p['datetime']),
                        message=process_name,
                        timestamp_desc=p['timestamp_desc'],
                        module=self.module_name,
                        data={'source': entity_type, 'uid': uid}
                    ).to_dict()
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type}. {e}")

    def __extract_ps_logdata_statistics_txt(self) -> Generator[dict, None, None]:
        """
        Extracts process data from logdata.statistics.txt.
        """
        entity_type = "logdata.statistics.txt"
        try:
            for p in LogDataStatisticsTxtParser(self.config, self.case_id).get_result():
                uid = p['data'].get('uid', p['data'].get('euid'))
                process_name = self._strip_flags(p['data']['process'])
                
                if self.add_if_full_path_is_not_in_set(process_name, uid):
                    yield Event(
                        datetime=datetime.fromisoformat(p['datetime']),
                        message=process_name,
                        timestamp_desc=p['timestamp_desc'],
                        module=self.module_name,
                        data={'source': entity_type, 'uid': uid}
                    ).to_dict()
        except Exception as e:
            logger.exception(f"ERROR while extracting {entity_type}. {e}")

    def add_if_full_path_is_not_in_set(self, name: str, uid: Optional[int] = None) -> bool:
        """
        Ensures that a process path with uid is unique before adding it to the shared set.

        :param name: Process path name
        :param uid: User ID (can be uid, euid, or auid)
        :return: True if the process was not in the set and was added, False otherwise.
        """
        key = (name, uid)
        
        # Check if this exact combination already exists
        if key in self.all_ps:
            return False
        
        # For backward compatibility, check if process exists without considering uid
        # when either the new or existing uid is None
        for item_name, item_uid in self.all_ps:
            if item_name.endswith(name):
                if uid is None or item_uid is None:
                    return False
            if item_name.split('::')[0].endswith(name):
                if uid is None or item_uid is None:
                    return False
            if '::' not in item_name and item_name.split(' ')[0].endswith(name):
                if uid is None or item_uid is None:
                    return False
        
        self.all_ps.add(key)
        return True

    def add_if_full_command_is_not_in_set(self, name: str, uid: Optional[int] = None) -> bool:
        """
        Ensures that a process command with uid is unique before adding it to the shared set.

        :param name: Process command name
        :param uid: User ID (can be uid, euid, or auid)
        :return: True if the process was not in the set and was added, False otherwise.
        """
        key = (name, uid)
        
        # Check if this exact combination already exists
        if key in self.all_ps:
            return False
        
        # For backward compatibility, check if process exists without considering uid
        # when either the new or existing uid is None
        for item_name, item_uid in self.all_ps:
            if item_name.startswith(name):
                if uid is None or item_uid is None:
                    return False
        
        self.all_ps.add(key)
        return True