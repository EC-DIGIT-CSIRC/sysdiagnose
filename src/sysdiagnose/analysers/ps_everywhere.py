#! /usr/bin/env python3

from typing import Generator
from sysdiagnose.utils.base import BaseAnalyserInterface, logger
from sysdiagnose.parsers.ps import PsParser
from sysdiagnose.parsers.psthread import PsThreadParser
from sysdiagnose.parsers.spindumpnosymbols import SpindumpNoSymbolsParser
from sysdiagnose.parsers.shutdownlogs import ShutdownLogsParser
from sysdiagnose.parsers.logarchive import LogarchiveParser
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
        self.all_ps = set()

    @staticmethod
    def _strip_flags(process: str) -> str:
        """
        Extracts the base command by removing everything after the first space.

        :param process: Full process command string.
        :return: Command string without flags.
        """
        process, *_ = process.partition(' ')
        return process

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
