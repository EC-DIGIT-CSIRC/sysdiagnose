#!/usr/bin/env python
import argparse
import sys
from sysdiagnose import Sysdiagnose
import os
import json
import logging
import time

logger = logging.getLogger('sysdiagnose')
logger.setLevel(logging.INFO)

def parse_parser_error(message):
    sd = Sysdiagnose()
    print(message, file=sys.stderr)
    print("Available parsers:")
    print("")
    sd.print_parsers_list()
    sys.exit(2)


def analyse_parser_error(message):
    sd = Sysdiagnose()
    print(message, file=sys.stderr)
    print("Available analysers:")
    print("")
    sd.print_analysers_list()
    sys.exit(2)

def get_console_logger(level: str) -> logging.StreamHandler:
    # Format
    fmt_console = logging.Formatter('[%(levelname)s] [%(module)s] %(message)s')
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt_console)

    return ch

def get_json_logger(filename: str) -> logging.FileHandler:
    # https://stackoverflow.com/questions/50144628/python-logging-into-file-as-a-dictionary-or-json
    fmt_json = logging.Formatter(
        json.dumps({
            'timestamp':'%(asctime)s',
            'level': '%(levelname)s',
            'module': '%(module)s',
            'message': '%(message)s'}))
    # File handler
    fh = logging.FileHandler(filename)
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt_json)

    return fh

def main():
    parser = argparse.ArgumentParser(
        prog='sysdiagnose',
        description='sysdiagnose parsing and analysis'
    )
    # available for all
    parser.add_argument('-c', '--case_id', required=False, default='all', help='ID of the case, or "all" for all cases (default)')

    subparsers = parser.add_subparsers(dest='mode')

    # init mode
    init_parser = subparsers.add_parser('init', help='Initialize a new case')
    init_parser.add_argument('filename', help='Name of the sysdiagnose archive file')
    init_parser.add_argument('--force', action='store_true', help='Force case creation')

    # parse mode
    parse_parser = subparsers.add_parser('parse', help='Parse a case')
    parse_parser.add_argument('parser', help='Name of the parser, "all" for running all parsers, or "list" for a listing of all parsers')
    parse_parser.add_argument('--log', default='WARNING', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Enables logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    parse_parser.error = parse_parser_error

    # analyse mode
    analyse_parser = subparsers.add_parser('analyse', help='Analyse a case')
    analyse_parser.add_argument('analyser', help='Name of the analyser, "all" for running all analysers, or "list" for a listing of all analysers')
    analyse_parser.add_argument('--log', default='WARNING', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Enables logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    analyse_parser.error = analyse_parser_error

    # list mode
    list_parser = subparsers.add_parser('list', help='List ...')
    list_parser.add_argument('what', choices=['cases', 'parsers', 'analysers'], help='List cases, parsers or analysers')
    list_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    # just for convenience
    cases_parser = subparsers.add_parser('cases', help='List cases')
    cases_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    subparsers.add_parser('parsers', help='List parsers')
    subparsers.add_parser('analysers', help='List analysers')

    parser.parse_args()

    args = parser.parse_args()

    sd = Sysdiagnose()

    if args.mode == 'list':
        if args.what == 'cases':
            sd.print_list_cases(verbose=args.verbose)
        elif args.what == 'parsers':
            sd.print_parsers_list()
        elif args.what == 'analysers':
            sd.print_analysers_list()

    elif args.mode == 'cases':
        sd.print_list_cases(verbose=args.verbose)

    elif args.mode == 'parsers':
        sd.print_parsers_list()

    elif args.mode == 'analysers':
        sd.print_analysers_list()

    elif args.mode == 'init':
        # Handle init mode
        filename = args.filename
        force = args.force

        if not os.path.isfile(filename) and filename.endswith('.tar.gz'):
            exit(f"File {filename} does not exist or is not a tar.gz file")
        # create the case
        try:
            if args.case_id and args.case_id != 'all':
                case_id = args.case_id
                sd.create_case(filename, force, case_id)
            else:
                case_id = sd.create_case(filename, force)['case_id']
        except Exception as e:
            exit(f"Error creating case: {str(e)}")

    elif args.mode == 'parse':
        # Handle parse mode
        if args.parser == 'list':
            sd.print_parsers_list()
            exit("")
        elif args.parser == 'all':
            parsers_list = list(sd.get_parsers().keys())
        elif not sd.is_valid_parser_name(args.parser):
            sd.print_parsers_list()
            print("")
            exit(f"Parser '{args.parser}' does not exist, possible options are listed above.")
        else:
            parsers_list = [args.parser]

        if args.case_id == 'all':
            case_ids = sd.get_case_ids()
        elif not sd.is_valid_case_id(args.case_id):
            sd.print_list_cases()
            print("")
            exit(f"Case ID '{args.case_id}' does not exist, possible options are listed above.")
        else:
            case_ids = [args.case_id]

        # Handle console logging
        log_level = args.log.upper()
        logger.addHandler(get_console_logger(log_level))

        logger2file = None
        for case_id in case_ids:
            # Handle file logging
            time_str = time.strftime("%Y%m%dT%H%M%S")
            filename = f"{time_str}-parse-{case_id}.jsonl"
            folder = sd.config.get_case_parsed_data_folder(case_id)
            # https://stackoverflow.com/questions/13839554/how-to-change-filehandle-with-python-logging-on-the-fly-with-different-classes-a
            if logger2file is None:
                logger2file = get_json_logger(os.path.join(folder, filename))
                logger.addHandler(logger2file)
            else:
                logger2file.close()
                logger2file.setStream(open(os.path.join(folder, filename), 'a'))

            print(f"Case ID: {case_id}")
            for parser in parsers_list:
                print(f"Parser '{parser}' for case ID '{case_id}'")
                logger.info(f"Parser '{parser}' started")
                try:
                    result = sd.parse(parser, case_id)
                    result_str = "successfully" if result == 0 else "with errors"
                    logger.info(f"Parser '{parser}' finished {result_str}")
                except NotImplementedError:
                    logger.warning(f"Parser '{parser}' is not implemented yet, skipping")

        if not logger2file is None:
            logger2file.close()

    elif args.mode == 'analyse':
        # Handle analyse mode
        if args.analyser == 'list':
            sd.print_analysers_list()
            exit("")
        elif args.analyser == 'all':
            analysers_list = list(sd.get_analysers().keys())
        elif not sd.is_valid_analyser_name(args.analyser):
            sd.print_analysers_list()
            print("")
            exit(f"Analyser '{args.analyser}' does not exist, possible options are listed above.")
        else:
            analysers_list = [args.analyser]

        if args.case_id == 'all':
            case_ids = sd.get_case_ids()
        elif not sd.is_valid_case_id(args.case_id):
            sd.print_list_cases()
            print("")
            exit(f"Case ID '{args.case_id}' does not exist, possible options are listed above.")
        else:
            case_ids = [args.case_id]

        # Handle console logging
        log_level = args.log.upper()
        logger.addHandler(get_console_logger(log_level))

        logger2file = None
        for case_id in case_ids:
            # Handle file logging
            time_str = time.strftime("%Y%m%dT%H%M%S")
            filename = f"{time_str}-analyse-{case_id}.jsonl"
            folder = sd.config.get_case_parsed_data_folder(case_id)
            # https://stackoverflow.com/questions/13839554/how-to-change-filehandle-with-python-logging-on-the-fly-with-different-classes-a
            if logger2file is None:
                logger2file = get_json_logger(os.path.join(folder, filename))
                logger.addHandler(logger2file)
            else:
                logger2file.close()
                logger2file.setStream(open(os.path.join(folder, filename), 'a'))

            print(f"Case ID: {case_id}")
            for analyser in analysers_list:
                print(f"  Analyser '{analyser}' for case ID '{case_id}'")
                logger.info(f"Analyser '{analyser}' started")
                try:
                    result = sd.analyse(analyser, case_id)
                    result_str = "successfully" if result == 0 else "with errors"
                    logger.info(f"Analyser '{analyser}' finished {result_str}")
                except NotImplementedError:
                    logger.warning(f"Analyser '{analyser}' is not implemented yet, skipping")

        if not logger2file is None:
            logger2file.close()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
