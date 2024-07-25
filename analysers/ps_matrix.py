#! /usr/bin/env python3
# make a matrix comparing, and showing visually
# TODO improve ps_matrix as it's not very useful right now

import json
import os
import pandas as pd
from tabulate import tabulate

analyser_description = "Makes a matrix comparing ps, psthread, taskinfo"
analyser_format = "txt"

uses_parsers = ['ps', 'psthread', 'taskinfo', 'spindumpnosymbols']


def analyse_path(case_folder: str, output_file: str = "ps_matrix.txt") -> bool:
    all_pids = set()

    with open(os.path.join(case_folder, "ps.json"), "r") as f:
        ps_json = json.load(f)
        ps_dict = {int(p['PID']): p for p in ps_json}
        all_pids.update(ps_dict.keys())

    with open(os.path.join(case_folder, "psthread.json"), "r") as f:
        psthread_json = json.load(f)
        psthread_dict = {int(p['PID']): p for p in psthread_json}
        all_pids.update(psthread_dict.keys())

    with open(os.path.join(case_folder, "taskinfo.json"), "r") as f:
        taskinfo_json = json.load(f)
        taskinfo_dict = {}
        for p in taskinfo_json['tasks']:
            taskinfo_dict[int(p['pid'])] = {
                'PID': p['pid']
            }
        all_pids.update(taskinfo_dict.keys())

    # not possible to use shutdownlogs as we're looking at different timeframes

    with open(os.path.join(case_folder, "spindumpnosymbols.json"), "r") as f:
        spindumpnosymbols_json = json.load(f)
        spindumpnosymbols_dict = {}
        for p in spindumpnosymbols_json['processes']:
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
    # print(tabulate(pd.DataFrame(matrix).T, headers='keys', tablefmt='psql'))
    with open(output_file, 'w') as f:
        f.write(tabulate(pd.DataFrame(matrix).T, headers='keys', tablefmt='psql'))

    return
