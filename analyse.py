#! /usr/bin/env python3

# For Python3
# Analyse the results produced by parsers

"""sysdiagnose analyse.

Usage:
  analyse.py list (cases|analysers)
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
        List available anlysers
    """
    os.chdir(folder)
    modules = glob.glob(os.path.join(os.path.dirname('.'), "*.py"))
    lines = []
    for analyser in modules:
        try:
            spec = importlib.util.spec_from_file_location(analyser[:-3], analyser)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            line = [analyser[:-3], module.analyser_description]
            lines.append(line)
        except:     # noqa: E722
            continue

    headers = ['Analyser Name', 'Parser Description']

    print(tabulate(lines, headers=headers))


def analyse(analyser, caseid):
    # Load parser module
    spec = importlib.util.spec_from_file_location(analyser[:-3], config.analysers_folder + "/" + analyser + '.py')
    print(spec, file=sys.stderr)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # building command
    parse_data_path = "%s/%s/" % (config.parsed_data_folder, caseid)
    output_file = config.parsed_data_folder + caseid + '/' + analyser + "." + module.analyser_format
    command = "module.%s('%s', '%s')" % (module.analyser_call, parse_data_path, output_file)
    result = eval(command)

    print(f'Execution success, output saved in: {output_file}')

    return 0


def allanalysers(caseid):
    os.chdir(config.analysers_folder)
    modules = glob.glob(os.path.join(os.path.dirname('.'), "*.py"))
    os.chdir('..')
    for analyser in modules:
        try:
            print('Trying: ' + analyser[:-3])
            analyse(analyser[:-3], caseid)
        except:     # noqa: E722
            continue
    return 0

# --------------------------------------------------------------------------- #


def main():
    """
    Main function
    """
    if sys.version_info[0] < 3:
        print("Must be using Python 3! Exiting ...")
        sys.exit(-1)

    arguments = docopt(__doc__, version=version_string)
    if arguments['list'] and arguments['cases']:
        parsing.list_cases(config.cases_file)
    elif arguments['list'] and arguments['analysers']:
        list_analysers(config.analysers_folder)
    elif arguments['analyse']:
        if arguments['<case_number>'].isdigit():
            analyse(arguments['<analyser>'], arguments['<case_number>'])
        else:
            print('case number should be ... a number ...')
    elif arguments['allanalysers']:
        if arguments['<case_number>'].isdigit():
            allanalysers(arguments['<case_number>'])
        else:
            print('case number should be ... a number ...')

    print("Running " + version_string + "\n")
    return


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folks ;)
