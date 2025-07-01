#! /usr/bin/env python3
# make a matrix comparing, and showing visually
# TODO improve ps_matrix as it's not very useful right now

import pandas as pd
from tabulate import tabulate
from sysdiagnose.utils.base import BaseAnalyserInterface, SysdiagnoseConfig
from sysdiagnose.parsers.ps import PsParser
from sysdiagnose.parsers.psthread import PsThreadParser
from sysdiagnose.parsers.taskinfo import TaskinfoParser
from sysdiagnose.parsers.spindumpnosymbols import SpindumpNoSymbolsParser


class PsMatrixAnalyser(BaseAnalyserInterface):
    description = "Makes a matrix comparing ps, psthread, taskinfo"
    format = "txt"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def execute(self):
        all_pids = set()

        ps_json = PsParser(self.config, self.case_id).get_result()
        ps_dict = {int(p['data']['pid']): p['data'] for p in ps_json}
        all_pids.update(ps_dict.keys())

        psthread_json = PsThreadParser(self.config, self.case_id).get_result()
        psthread_dict = {int(p['data']['pid']): p['data'] for p in psthread_json}
        all_pids.update(psthread_dict.keys())

        taskinfo_json = TaskinfoParser(self.config, self.case_id).get_result()
        taskinfo_dict = {}
        for p in taskinfo_json:
            if 'pid' not in p['data']:
                continue
            taskinfo_dict[int(p['data']['pid'])] = {
                'pid': p['data']['pid']
            }
        all_pids.update(taskinfo_dict.keys())

        # not possible to use shutdownlogs as we're looking at different timeframes

        spindumpnosymbols_json = SpindumpNoSymbolsParser(self.config, self.case_id).get_result()
        spindumpnosymbols_dict = {}
        for p in spindumpnosymbols_json:
            if 'process' not in p['data']:
                continue
            spindumpnosymbols_dict[int(p['data']['pid'])] = {
                'pid': p['data']['pid'],
                'ppid': p['data'].get('ppid', ''),
                'command': p['data'].get('path', ''),
            }

        matrix = {}
        all_pids = list(all_pids)
        all_pids.sort()
        for pid in all_pids:
            matrix[pid] = {
                'cmd': ps_dict.get(pid, {}).get('command'),
            }

            # '%CPU', '%MEM', 'F', 'NI',
            # 'PRI', 'RSS',
            # 'STARTED', 'STAT', 'TIME', 'TT', 'USER', 'VSZ'
            for col in ['pid']:
                ps_val = str(ps_dict.get(pid, {}).get(col))
                psthread_val = str(psthread_dict.get(pid, {}).get(col))
                taskinfo_val = str(taskinfo_dict.get(pid, {}).get(col))
                spindump_val = str(spindumpnosymbols_dict.get(pid, {}).get(col))

                cmpr = ps_val == psthread_val == taskinfo_val == spindump_val
                if cmpr:
                    matrix[pid][col] = True
                else:  # different
                    matrix[pid][col] = f"{ps_val} != {psthread_val} != {taskinfo_val} != {spindump_val}"

            for col in ['ppid']:
                ps_val = str(ps_dict.get(pid, {}).get(col))
                psthread_val = str(psthread_dict.get(pid, {}).get(col))
                spindump_val = str(spindumpnosymbols_dict.get(pid, {}).get(col))

                cmpr = ps_val == psthread_val == spindump_val
                if cmpr:
                    matrix[pid][col] = True
                else:  # different
                    matrix[pid][col] = f"{ps_val} != {psthread_val} != {spindump_val}"

        # LATER consider filtering the table to only show differences
        return tabulate(pd.DataFrame(matrix).T, headers='keys', tablefmt='psql')
