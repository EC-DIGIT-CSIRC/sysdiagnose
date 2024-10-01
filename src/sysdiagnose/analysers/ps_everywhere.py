#! /usr/bin/env python3

from sysdiagnose.utils.base import BaseAnalyserInterface
from sysdiagnose.parsers.ps import PsParser
from sysdiagnose.parsers.psthread import PsThreadParser
from sysdiagnose.parsers.spindumpnosymbols import SpindumpNoSymbolsParser
from sysdiagnose.parsers.shutdownlogs import ShutdownLogsParser
from sysdiagnose.parsers.logarchive import LogarchiveParser
from sysdiagnose.parsers.uuid2path import UUID2PathParser
from sysdiagnose.parsers.taskinfo import TaskinfoParser
from sysdiagnose.parsers.remotectl_dumpstate import RemotectlDumpstateParser


class PsEverywhereAnalyser(BaseAnalyserInterface):
    description = "List all processes we can find a bit everywhere."
    format = "json"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)
        self.all_ps = set()

    def execute(self):
        # the order of below is important: we want to have the most detailed information first
        # - first processes with full path and parameters
        # - then processes with full path and no parameters
        # - then processes no full path and no parameters

        # processes with full path and parameters, no threads
        ps_json = PsParser(self.config, self.case_id).get_result()
        self.all_ps.update([p['COMMAND'] for p in ps_json])
        print(f"{len(self.all_ps)} entries after ps")

        # processes with full path and parameters

        psthread_json = PsThreadParser(self.config, self.case_id).get_result()
        self.all_ps.update([p['COMMAND'] for p in psthread_json])
        print(f"{len(self.all_ps)} entries after psthread")

        # processes with full path, no parameters, with threads
        spindumpnosymbols_json = SpindumpNoSymbolsParser(self.config, self.case_id).get_result()
        for p in spindumpnosymbols_json:
            if 'Process' not in p:
                continue
            try:
                self.add_if_full_command_is_not_in_set(p['Path'])
                # all_ps.add(f"{p['Path']}::#{len(p['threads'])}") # count is different than in taskinfo
            except KeyError:
                if p['Process'] == 'kernel_task [0]':
                    self.all_ps.add('/kernel')  # is similar to the other formats
                else:
                    self.add_if_full_command_is_not_in_set(p['Process'])  # backup uption to keep trace of this anomaly
            for t in p['threads']:
                try:
                    self.add_if_full_command_is_not_in_set(f"{p['Path']}::{t['ThreadName']}")
                except KeyError:
                    pass
        print(f"{len(self.all_ps)} entries after spindumpnosymbols")

        # processes with full path, no parameters, no threads
        shutdownlogs_json = ShutdownLogsParser(self.config, self.case_id).get_result()
        for p in shutdownlogs_json:
            # not using 'path' but 'command', as the path being appended by the UUID will be counter productive to normalisation
            self.add_if_full_command_is_not_in_set(p['command'])
        print(f"{len(self.all_ps)} entries after shutdownlogs")

        # processes with full path, no parameters, no threads
        logarchive_procs = set()
        for event in LogarchiveParser(self.config, self.case_id).get_result():
            try:
                logarchive_procs.add(event['process'])
            except KeyError:
                pass

        for entry in logarchive_procs:
            self.add_if_full_command_is_not_in_set(entry)
        print(f"{len(self.all_ps)} entries after logarchive")

        # processes with full path, no parameters, no threads
        uuid2path_json = UUID2PathParser(self.config, self.case_id).get_result()
        for item in uuid2path_json.values():
            self.add_if_full_command_is_not_in_set(item)
        print(f"{len(self.all_ps)} entries after uuid2path")

        # processes no full path, no parameters, with threads
        taskinfo_json = TaskinfoParser(self.config, self.case_id).get_result()
        # p['name'] is the short version of COMMAND, so incompatible with the other formats.
        # on the other hand it may contain valuable stuff, so we use it in 2 formats
        # - name::#num_of_threads
        # - name::thread name
        for p in taskinfo_json:
            if 'name' not in p:
                continue
            self.add_if_full_path_is_not_in_set(p['name'])
            # add_if_full_path_is_not_in_set(f"{p['name']}::#{len(p['threads'])}") # count is different than in spindumpnosymbols
            for t in p['threads']:
                try:
                    self.add_if_full_path_is_not_in_set(f"{p['name']}::{t['thread name']}")
                except KeyError:
                    pass
        print(f"{len(self.all_ps)} entries after taskinfo")

        # processes no full path, no parameters, no threads
        remotectl_dumpstate_json = RemotectlDumpstateParser(self.config, self.case_id).get_result()
        if remotectl_dumpstate_json:
            for p in remotectl_dumpstate_json['Local device']['Services']:
                self.add_if_full_path_is_not_in_set(p)

        print(f"{len(self.all_ps)} entries after remotectl_dumpstate")

        self.all_ps = list(self.all_ps)
        self.all_ps.sort()
        return self.all_ps

    def add_if_full_path_is_not_in_set(self, name: str):
        for item in self.all_ps:
            # no need to add it in the following cases
            if item.endswith(name):
                return
            if item.split('::').pop(0).endswith(name):
                return
            if '::' not in item and item.split(' ').pop(0).endswith(name):
                # this will but with commands that have a space, but looking at data this should not happend often
                return
        self.all_ps.add(name)

    def add_if_full_command_is_not_in_set(self, name: str):
        for item in self.all_ps:
            if item.startswith(name):
                # no need to add it
                return
        self.all_ps.add(name)
