#! /usr/bin/env python3

# For Python3
# Analyse the results produced by parsers

"""sysdiagnose analyse.

Usage:
  analyse.py list (cases|analysers|all)
  analyse.py analyse <analyser> <case_number>
  analyse.py allanalysers <case_number>
  analyse.py (-h | --help)
  analyse.py --version

Options:
  -h --help     Show this screen.
  -v --version     Show version.
"""

import config
import parsing

import os
import sys
import glob
import importlib.util
from docopt import docopt
from tabulate import tabulate

version_string = "analyse.py v2023-04-27 Version 1.0"


def list_analysers(folder):
    """
        List available analysers
    """
    prev_folder = os.getcwd()
    os.chdir(folder)
    modules = glob.glob(os.path.join(os.path.dirname('.'), "*.py"))
    lines = []
    for analyser in modules:
        if analyser.endswith('__init__.py'):
            continue
        try:
            spec = importlib.util.spec_from_file_location(analyser[:-3], analyser)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            line = [analyser[:-3], module.analyser_description]
            lines.append(line)
        except AttributeError:
            continue

    headers = ['Analyser Name', 'Analyser Description']

    print(tabulate(lines, headers=headers))
    os.chdir(prev_folder)


def analyse(analyser, caseid):
    # Load parser module
    spec = importlib.util.spec_from_file_location(analyser[:-3], os.path.join(config.analysers_folder, analyser + '.py'))
    # print(spec, file=sys.stderr)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # building command
    parse_data_path = "%s/%s/" % (config.parsed_data_folder, caseid)
    # TODO consider outputting anlaysers output to a different folder defined in config.py
    output_file = os.path.join(config.parsed_data_folder, caseid, analyser + "." + module.analyser_format)
    module.analyse_path(case_folder=parse_data_path, output_file=output_file)
    print(f'Execution success, output saved in: {output_file}', file=sys.stderr)

    return 0


def allanalysers(caseid):
    prev_folder = os.getcwd()
    os.chdir(config.analysers_folder)
    modules = glob.glob(os.path.join(os.path.dirname('.'), "*.py"))
    os.chdir('..')
    for analyser in modules:
        if analyser.endswith('__init__.py') or analyser.endswith('demo_analyser.py'):
            continue
        try:
            print(f'Trying: {analyser[:-3]}', file=sys.stderr)
            analyse(analyser[:-3], caseid)
        except Exception as e:     # noqa: E722
            import traceback
            print(f"Error: Problem while executing module {analyser[:-3]}. Reason: {str(e)}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            continue
    os.chdir(prev_folder)
    return 0

# --------------------------------------------------------------------------- #


def main():
    """
    Main function
    """
    if sys.version_info[0] < 3:
        print("Must be using Python 3! Exiting ...", file=sys.stderr)
        sys.exit(-1)

    arguments = docopt(__doc__, version=version_string)
    if arguments['list'] and arguments['cases']:
        parsing.list_cases()
    elif arguments['list'] and arguments['analysers']:
        list_analysers(config.analysers_folder)
    elif arguments['list']:
        list_analysers(config.analysers_folder)
        print("\n")
        parsing.list_cases()
    elif arguments['analyse']:
        if arguments['<case_number>'].isdigit():
            analyse(arguments['<analyser>'], arguments['<case_number>'])
        else:
            print("case number should be ... a number ...", file=sys.stderr)
    elif arguments['allanalysers']:
        if arguments['<case_number>'].isdigit():
            allanalysers(arguments['<case_number>'])
        else:
            print("case number should be ... a number ...", file=sys.stderr)
    return


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folks ;)
