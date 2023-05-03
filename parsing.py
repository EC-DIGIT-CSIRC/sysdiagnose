#! /usr/bin/env python3

# For Python3
# Parsing sysdiagnose extracted files
# Parse extracted files
# Also contains listing of existing cases and available parsers

"""sysdiagnose parse.

Usage:
  parsing.py list (cases|parsers)
  parsing.py parse <parser> <case_number>
  parsing.py allparsers <case_number>
  parsing.py (-h | --help)
  parsing.py --version

Options:
  -h --help     Show this screen.
  -v --version     Show version.
"""

import config

import json
import os
import sys
import importlib.util
import glob
from tabulate import tabulate
from docopt import docopt


"""
    List cases
"""


def list_cases(case_file):
    try:
        with open(config.cases_file, 'r') as f:
            cases = json.load(f)
    except Exception as e:
        print(f'error opening cases json file - check config.py. Reason: {str(e)}', file=sys.stderr)
        sys.exit()

    print('#### case List ####')
    headers = ['Case ID', 'Source file', 'SHA256']
    lines = []
    for case in cases['cases']:
        line = [case['case_id'], case['source_file'], case['source_sha256']]
        lines.append(line)

    print(tabulate(lines, headers=headers))


"""
    List parsers
"""


def list_parsers(folder):
    os.chdir(folder)
    modules = glob.glob(os.path.join(os.path.dirname('.'), "*.py"))
    lines = []
    for parser in modules:
        try:
            spec = importlib.util.spec_from_file_location(parser[:-3], parser)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            line = [parser[:-3], module.parser_description, module.parser_input]
            lines.append(line)
        except:     # noqa: E722
            continue

    headers = ['Parser Name', 'Parser Description', 'Parser Input']

    print(tabulate(lines, headers=headers))


"""
    Parse
"""


def parse(parser, case_id):
    try:
        with open(config.cases_file, 'r') as f:
            cases = json.load(f)
    except Exception as e:
        print(f'error opening cases json file - check config.py. Error: {str(e)}', file=sys.stderr)
        sys.exit()

    case_file = ''
    for case in cases['cases']:
        if int(case_id) == case['case_id']:
            case_file = case['case_file']

    if case_file == '':
        print('Case ID not found', file=sys.stderr)
        sys.exit()

    # Load case file
    try:
        with open(case_file, 'r') as f:
            case = json.load(f)
    except:     # noqa: E722
        print('error opening case file', file=sys.stderr)
        sys.exit()

    # print(json.dumps(case, indent=4), file=sys.stderr)   #debug

    # Load parser module
    spec = importlib.util.spec_from_file_location(parser[:-3], config.parsers_folder + parser + '.py')
    print(spec, file=sys.stderr)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # building command
    if type(case[module.parser_input]) == str:
        command = 'module.' + module.parser_call + '(\'' + case[module.parser_input] + '\')'
    else:
        command = 'module.' + module.parser_call + '(' + str(case[module.parser_input]) + ')'

    # running the command, expecting JSON output
    # try:
    #    result = eval(command)
    # except Exception as e:
    #    print(f'Error trying to parse {case[module.parser_input]}: {str(e)}', file=sys.stderr)

    result = eval(command)

    # saving the parser output
    output_file = config.parsed_data_folder + case_id + '/' + parser + '.json'
    with open(output_file, 'w') as data_file:
        data_file.write(json.dumps(result, indent=4))

    print(f'Execution success, output saved in: {output_file}', file=sys.stderr)

    return 0


"""
    Parse All
"""


def parse_all(case_id):
    # get list of working parsers
    # for each parser, run and save which is working
    # display list of successful parses
    os.chdir(config.parsers_folder)
    modules = glob.glob(os.path.join(os.path.dirname('.'), "*.py"))
    os.chdir('..')
    for parser in modules:
        try:
            print('Trying: ' + parser[:-3], file=sys.stderr)
            parse(parser[:-3], case_id)
        except:     # noqa: E722
            continue
    return 0


"""
    Main function
"""


def main():

    if sys.version_info[0] < 3:
        print("Still using Python 2 ?!?", file=sys.stderr)
        sys.exit(-1)

    arguments = docopt(__doc__, version='Sysdiagnose parsing script v0.1')

    # print(arguments, file=sys.stderr)

    if arguments['list'] and arguments['cases']:
        list_cases(config.cases_file)
    elif arguments['list'] and arguments['parsers']:
        list_parsers(config.parsers_folder)
    elif arguments['parse']:
        if arguments['<case_number>'].isdigit():
            parse(arguments['<parser>'], arguments['<case_number>'])
        else:
            print('case number should be ... a number ...', file=sys.stderr)
    elif arguments['allparsers']:
        if arguments['<case_number>'].isdigit():
            parse_all(arguments['<case_number>'])
        else:
            print('case number should be ... a number ...', file=sys.stderr)


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()
