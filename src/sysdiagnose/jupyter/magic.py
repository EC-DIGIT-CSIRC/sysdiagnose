#! /usr/bin/env python3

# Sysdiagnose Jupyter magic commands
# Author: EC-DIGIT-CSIRC

"""
IPython magic commands for sysdiagnose.

Provides %sd magic for interactive case management, parsing, and analysis.
"""
import os

from IPython.core.magic import Magics, line_magic, magics_class

from sysdiagnose import Sysdiagnose
from sysdiagnose.jupyter.display import (
    analysers_to_df,
    case_info_to_df,
    cases_to_df,
    parsers_to_df,
    result_to_df,
)
from sysdiagnose.utils.logger import logger


@magics_class
class SysdiagnoseMagic(Magics):
    """
    Sysdiagnose magic commands for Jupyter notebooks.

    Usage:
        %sd cases                  - List all cases
        %sd use <case_id>          - Set active case
        %sd info                   - Show active case info
        %sd parsers                - List available parsers
        %sd analysers              - List available analysers
        %sd parse <name>           - Run parser (result stored in _sd_result)
        %sd analyse <name>         - Run analyser (result stored in _sd_result)
        %sd load <name>            - Load cached parser/analyser result as DataFrame
        %sd help                   - Show this help
    """

    _instance = None

    def __init__(self, shell):
        super().__init__(shell)
        cases_path = os.getenv('SYSDIAGNOSE_CASES_PATH', './cases')
        self.sd = Sysdiagnose(cases_path=cases_path)
        self.case_id = None
        SysdiagnoseMagic._instance = self

    @classmethod
    def instance(cls):
        return cls._instance

    @line_magic
    def sd(self, line):
        """Main entry point for sysdiagnose magic commands."""
        args = line.strip().split()
        cmd = args[0] if args else 'help'

        dispatch = {
            'cases': self._cmd_cases,
            'use': self._cmd_use,
            'info': self._cmd_info,
            'parsers': self._cmd_parsers,
            'analysers': self._cmd_analysers,
            'parse': self._cmd_parse,
            'analyse': self._cmd_analyse,
            'load': self._cmd_load,
            'help': self._cmd_help,
        }

        handler = dispatch.get(cmd, self._cmd_help)
        return handler(args[1:])

    def _require_case(self):
        if not self.case_id:
            print("No active case. Use: %sd use <case_id>")
            return False
        return True

    def _cmd_cases(self, _args):
        return cases_to_df(self.sd)

    def _cmd_use(self, args):
        if not args:
            print("Usage: %sd use <case_id>")
            return None
        case_id = args[0]
        if not self.sd.is_valid_case_id(case_id):
            print(f"Case '{case_id}' not found. Use %sd cases to list available cases.")
            return None
        self.case_id = case_id
        print(f"Active case: {case_id}")
        return case_info_to_df(self.sd, case_id)

    def _cmd_info(self, _args):
        if not self._require_case():
            return None
        return case_info_to_df(self.sd, self.case_id)

    def _cmd_parsers(self, _args):
        return parsers_to_df(self.sd)

    def _cmd_analysers(self, _args):
        return analysers_to_df(self.sd)

    def _cmd_parse(self, args):
        if not self._require_case():
            return None
        if not args:
            print("Usage: %sd parse <parser_name>")
            return self._cmd_parsers([])
        name = args[0]
        if name == 'all':
            for parser_name in self.sd.config.get_parsers():
                print(f"  Parsing: {parser_name}...")
                try:
                    self.sd.parse(parser_name, self.case_id)
                except Exception:
                    logger.exception(f"Error running parser '{parser_name}'")
            print("Done.")
            return None
        if not self.sd.is_valid_parser_name(name):
            print(f"Parser '{name}' not found.")
            return self._cmd_parsers([])
        print(f"Running parser '{name}' on case '{self.case_id}'...")
        self.sd.parse(name, self.case_id)
        print("Done.")
        return self._cmd_load([name])

    def _cmd_analyse(self, args):
        if not self._require_case():
            return None
        if not args:
            print("Usage: %sd analyse <analyser_name>")
            return self._cmd_analysers([])
        name = args[0]
        if name == 'all':
            for analyser_name in self.sd.config.get_analysers():
                print(f"  Analysing: {analyser_name}...")
                try:
                    self.sd.analyse(analyser_name, self.case_id)
                except Exception:
                    logger.exception(f"Error running analyser '{analyser_name}'")
            print("Done.")
            return None
        if not self.sd.is_valid_analyser_name(name):
            print(f"Analyser '{name}' not found.")
            return self._cmd_analysers([])
        print(f"Running analyser '{name}' on case '{self.case_id}'...")
        self.sd.analyse(name, self.case_id)
        print("Done.")
        return self._cmd_load([name])

    def _cmd_load(self, args):
        """Load a parsed/analysed result as a DataFrame."""
        if not self._require_case():
            return None
        if not args:
            print("Usage: %sd load <parser_or_analyser_name>")
            return None
        name = args[0]
        parsed_folder = self.sd.config.get_case_parsed_data_folder(self.case_id)
        df = result_to_df(parsed_folder, name)
        if df is not None:
            var_name = f"sd_{name}"
            self.shell.user_ns[var_name] = df
            self.shell.user_ns['_sd_result'] = df
            print(f"Result loaded into '{var_name}' and '_sd_result' ({len(df)} rows)")
        return df

    def _cmd_help(self, _args=None):
        print(self.__class__.__doc__)
