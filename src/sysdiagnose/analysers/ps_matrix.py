#! /usr/bin/env python3
# make a matrix comparing, and showing visually
# TODO improve ps_matrix as it's not very useful right now

import pandas as pd
from tabulate import tabulate
from sysdiagnose.utils.base import BaseAnalyserInterface
from sysdiagnose.parsers.ps import PsParser
from sysdiagnose.parsers.psthread import PsThreadParser
from sysdiagnose.parsers.taskinfo import TaskinfoParser
from sysdiagnose.parsers.spindumpnosymbols import SpindumpNoSymbolsParser


class PsMatrixAnalyser(BaseAnalyserInterface):
    description = "Makes a matrix comparing ps, psthread, taskinfo"
    format = "txt"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def execute(self):
        all_pids = set()

        ps_json = PsParser(self.config, self.case_id).get_result()
        ps_dict = {int(p['PID']): p for p in ps_json}
        all_pids.update(ps_dict.keys())

        psthread_json = PsThreadParser(self.config, self.case_id).get_result()
        psthread_dict = {int(p['PID']): p for p in psthread_json}
        all_pids.update(psthread_dict.keys())

        taskinfo_json = TaskinfoParser(self.config, self.case_id).get_result()
        taskinfo_dict = {}
        for p in taskinfo_json:
            if 'pid' not in p:
                continue
            taskinfo_dict[int(p['pid'])] = {
                'PID': p['pid']
            }
        all_pids.update(taskinfo_dict.keys())

        # not possible to use shutdownlogs as we're looking at different timeframes

        spindumpnosymbols_json = SpindumpNoSymbolsParser(self.config, self.case_id).get_result()
        spindumpnosymbols_dict = {}
        for p in spindumpnosymbols_json:
            if 'Process' not in p:
                continue
            spindumpnosymbols_dict[int(p['PID'])] = {
                'PID': p['PID'],
                'PPID': p.get('PPID', ''),
                'COMMAND': p.get('Path', ''),
            }

        matrix = {}
        all_pids = list(all_pids)
        all_pids.sort()
        for pid in all_pids:
            matrix[pid] = {
                'cmd': ps_dict.get(pid, {}).get('COMMAND'),
            }

            # '%CPU', '%MEM', 'F', 'NI',
            # 'PRI', 'RSS',
            # 'STARTED', 'STAT', 'TIME', 'TT', 'USER', 'VSZ'
            for col in ['PID']:
                ps_val = str(ps_dict.get(pid, {}).get(col))
                psthread_val = str(psthread_dict.get(pid, {}).get(col))
                taskinfo_val = str(taskinfo_dict.get(pid, {}).get(col))
                spindump_val = str(spindumpnosymbols_dict.get(pid, {}).get(col))

                cmpr = ps_val == psthread_val == taskinfo_val == spindump_val
                if cmpr:
                    matrix[pid][col] = True
                else:  # different
                    matrix[pid][col] = f"{ps_val} != {psthread_val} != {taskinfo_val} != {spindump_val}"

            for col in ['PPID']:
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
