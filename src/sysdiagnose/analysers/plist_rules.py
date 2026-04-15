import glob
import json
import os

import yara
from sysdiagnose.utils.base import BaseAnalyserInterface, Event, SysdiagnoseConfig, logger
from sysdiagnose.parsers.plists import PlistParser


# Externals stub so YARA rules using these variables can load
externals = {
    'filename': '',
    'filepath': '',
    'extension': '',
}


class PlistRulesAnalyser(BaseAnalyserInterface):
    description = "Scan parsed plist files using YARA rules for structured extraction ('./yara/plist' or SYSDIAGNOSE_PLIST_RULES_PATH)"
    format = "jsonl"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)
        self.yara_rules_path = os.getenv('SYSDIAGNOSE_PLIST_RULES_PATH', './yara/plist')
        self.parser = PlistParser(config, case_id)

    def execute(self) -> list:
        # Ensure plists are parsed first
        self.parser.save_result()

        rule_filepaths = self._get_valid_yara_rule_files()
        rules = yara.compile(filepaths=rule_filepaths, externals=externals)

        results = []
        plist_json_files = glob.glob(os.path.join(self.parser.output_folder, '*.json'))

        for json_file in plist_json_files:
            file_externals = {
                'filename': os.path.basename(json_file),
                'filepath': json_file,
                'extension': '.json',
            }
            # Compile with per-file externals for rules that use them
            file_rules = yara.compile(filepaths=rule_filepaths, externals=file_externals)

            try:
                matches = file_rules.match(json_file)
            except yara.Error:
                logger.exception(f"Error scanning plist file {json_file}")
                continue

            if not matches:
                continue

            logger.info(f"YARA matched {len(matches)} rule(s) in {json_file}",
                        extra={'plist_rules_target': json_file, 'match_count': len(matches)})

            # Load the full structured plist data for this file
            plist_data = self._load_plist_json(json_file)

            # Derive the original plist relative path from the json filename
            # The plists parser replaces '/' with '_' and appends '.json'
            plist_relative_path = os.path.basename(json_file).removesuffix('.json').replace('_', '/')

            for match in matches:
                data = {
                    'plist_file': plist_relative_path,
                    'plist_data': plist_data,
                    'yara_rule_file': match.namespace,
                    'yara_rule': match.rule,
                    'yara_rule_meta': match.meta,
                    'yara_rule_tags': match.tags,
                    'yara_match_strings': [
                        {
                            'identifier': s.identifier,
                            'instances': [
                                {
                                    'offset': inst.offset,
                                    'plaintext': inst.plaintext().decode(errors='replace'),
                                }
                                for inst in s.instances
                            ]
                        }
                        for s in match.strings
                    ],
                }

                message = f"Plist YARA rule '{match.rule}' from {match.namespace} matched in {plist_relative_path}"
                event = Event(
                    datetime=self.sysdiagnose_creation_datetime,
                    message=message,
                    module=self.module_name,
                    timestamp_desc='Sysdiagnose creation datetime',
                    data=data,
                )
                results.append(event.to_dict())

        return results

    def _get_valid_yara_rule_files(self) -> dict:
        """Load and validate YARA rule files from the plist rules directory."""
        if not os.path.isdir(self.yara_rules_path):
            raise FileNotFoundError(
                f"Plist YARA rules folder not found: {self.yara_rules_path}. "
                f"Create it or set SYSDIAGNOSE_PLIST_RULES_PATH."
            )

        rule_filepaths = {}
        for rule_file in glob.glob(os.path.join(self.yara_rules_path, '**', '*.yar'), recursive=True):
            if not os.path.isfile(rule_file):
                continue
            try:
                yara.compile(filepath=rule_file, externals=externals)
                namespace = rule_file[len(self.yara_rules_path):].strip(os.path.sep)
                rule_filepaths[namespace] = rule_file
                logger.info(f"Loaded plist YARA rule: {rule_file}")
            except yara.SyntaxError:
                logger.exception(f"Syntax error in plist YARA rule {rule_file}")
            except yara.Error:
                logger.exception(f"Error compiling plist YARA rule {rule_file}")

        if not rule_filepaths:
            raise ValueError(
                f"No valid YARA rules (.yar) found in: {self.yara_rules_path}"
            )
        return rule_filepaths

    @staticmethod
    def _load_plist_json(json_file: str) -> dict | list | None:
        """Load a parsed plist JSON file, returning None on error."""
        try:
            with open(json_file, 'r') as f:
                return json.load(f)
        except Exception:
            logger.exception(f"Error loading plist JSON {json_file}")
            return None
