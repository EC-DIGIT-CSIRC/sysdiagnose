#! /usr/bin/env python3

import json
import os

analyser_description = "List all processes we can find a bit everywhere."
analyser_format = "json"


def analyse_path(case_folder: str, output_file: str = "ps_everywhere.json") -> bool:
    all_ps = set()

    # the order of below is important: we want to have the most detailed information first
    # - first processes with full path and parameters
    # - then processes with full path and no parameters
    # - then processes no full path and no parameters

    # processes with full path and parameters, no threads
    with open(os.path.join(case_folder, "ps.json"), "r") as f:
        ps_json = json.load(f)
        all_ps.update([p['COMMAND'] for p in ps_json])
    print(f"{len(all_ps)} entries after ps")

    # processes with full path and parameters
    with open(os.path.join(case_folder, "psthread.json"), "r") as f:
        psthread_json = json.load(f)
        all_ps.update([p['COMMAND'] for p in psthread_json])
    print(f"{len(all_ps)} entries after psthread")

    # processes with full path, no parameters, with threads
    with open(os.path.join(case_folder, "spindumpnosymbols.json"), "r") as f:
        spindumpnosymbols_json = json.load(f)
        for p in spindumpnosymbols_json['processes']:
            try:
                add_if_full_command_is_not_in_set(p['Path'], all_ps)
                # all_ps.add(f"{p['Path']}::#{len(p['threads'])}") # count is different than in taskinfo
            except KeyError:
                if p['Process'] == 'kernel_task [0]':
                    all_ps.add('/kernel')  # is similar to the other formats
                else:
                    add_if_full_command_is_not_in_set(p['Process'], all_ps)  # backup uption to keep trace of this anomaly
            for t in p['threads']:
                try:
                    add_if_full_command_is_not_in_set(f"{p['Path']}::{t['ThreadName']}", all_ps)
                except KeyError:
                    pass
    print(f"{len(all_ps)} entries after spindumpnosymbols")

    # processes with full path, no parameters, no threads
    with open(os.path.join(case_folder, "shutdownlogs.json"), "r") as f:
        shutdownlogs_json = json.load(f)
        for section in shutdownlogs_json.values():
            # not using 'path' but 'command', as the path being appended by the UUID will be counter productive to normalisation
            for p in section:
                add_if_full_command_is_not_in_set(p['command'], all_ps)
    print(f"{len(all_ps)} entries after shutdownlogs")

    # processes with full path, no parameters, no threads
    with open(os.path.join(case_folder, "logarchive.json"), "r") as f:
        logarchive_procs = set()
        for line in f:
            event = json.loads(line)
            try:
                logarchive_procs.add(event['process'])
            except KeyError:
                pass

        for entry in logarchive_procs:
            add_if_full_command_is_not_in_set(entry, all_ps)
    print(f"{len(all_ps)} entries after logarchive")

    # processes with full path, no parameters, no threads
    with open(os.path.join(case_folder, "uuid2path.json"), "r") as f:
        uuid2path_json = json.load(f)
        for item in uuid2path_json.values():
            add_if_full_command_is_not_in_set(item, all_ps)
    print(f"{len(all_ps)} entries after uuid2path")

    # processes no full path, no parameters, with threads
    with open(os.path.join(case_folder, "taskinfo.json"), "r") as f:
        taskinfo_json = json.load(f)
        # p['name'] is the short version of COMMAND, so incompatible with the other formats.
        # on the other hand it may contain valuable stuff, so we use it in 2 formats
        # - name::#num_of_threads
        # - name::thread name
        for p in taskinfo_json['tasks']:
            add_if_full_path_is_not_in_set(p['name'], all_ps)
            # add_if_full_path_is_not_in_set(f"{p['name']}::#{len(p['threads'])}") # count is different than in spindumpnosymbols
            for t in p['threads']:
                try:
                    add_if_full_path_is_not_in_set(f"{p['name']}::{t['thread name']}", all_ps)
                except KeyError:
                    pass
    print(f"{len(all_ps)} entries after taskinfo")

    # processes no full path, no parameters, no threads
    with open(os.path.join(case_folder, "remotectl_dumpstate.json"), "r") as f:
        remotectl_dumpstate_json = json.load(f)
        for p in remotectl_dumpstate_json['Local device']['Services']:
            add_if_full_path_is_not_in_set(p, all_ps)

    print(f"{len(all_ps)} entries after remotectl_dumpstate")

    all_ps = list(all_ps)
    all_ps.sort()
    with open(output_file, 'w') as f:
        json.dump(all_ps, f, indent=4)
    return


def add_if_full_path_is_not_in_set(name: str, all_ps: set):
    for item in all_ps:
        # no need to add it in the following cases
        if item.endswith(name):
            return
        if item.split('::').pop(0).endswith(name):
            return
        if '::' not in item and item.split(' ').pop(0).endswith(name):
            # this will but with commands that have a space, but looking at data this should not happend often
            return
    all_ps.add(name)


def add_if_full_command_is_not_in_set(name: str, all_ps: set):
    for item in all_ps:
        if item.startswith(name):
            # no need to add it
            return
    all_ps.add(name)
