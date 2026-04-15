import glob
import json
import os

import yara
from sysdiagnose.utils.base import BaseAnalyserInterface, Event, SysdiagnoseConfig, logger
from sysdiagnose.analysers.yarascan import YaraAnalyser
from sysdiagnose.parsers.plists import PlistParser

# Minimal externals stub — plist JSON files don't need filetype/owner
externals = {
    'filename': '',
    'filepath': '',
    'extension': '',
    'filetype': '',
    'owner': '',
}


class PlistRulesAnalyser(BaseAnalyserInterface):
    description = "Scan parsed plist files using YARA rules for structured extraction ('./yara/plist' or SYSDIAGNOSE_PLIST_RULES_PATH)"
    format = "jsonl"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)
        self.yara_rules_path = os.getenv('SYSDIAGNOSE_PLIST_RULES_PATH', './yara/plist')
        self.parser = PlistParser(config, case_id)

    def execute(self) -> list:
        # Ensure plists are parsed to JSON first
        self.parser.save_result()

        rule_filepaths = YaraAnalyser.load_valid_yara_rule_files(self.yara_rules_path, externals)
        rules = yara.compile(filepaths=rule_filepaths, externals=externals)

        results = []
        for json_file in glob.glob(os.path.join(self.parser.output_folder, '*.json')):
            try:
                matches = rules.match(json_file)
            except yara.Error:
                logger.exception(f"Error scanning plist file {json_file}")
                continue

            if not matches:
                continue

            # Load the full structured plist data on match
            plist_data = PlistRulesAnalyser._load_json(json_file)

            # Derive original plist relative path from json filename
            # The plists parser replaces '/' with '_' and appends '.json'
            plist_relative_path = os.path.basename(json_file).removesuffix('.json').replace('_', '/')

            logger.info(f"YARA matched {len(matches)} rule(s) in {plist_relative_path}",
                        extra={'plist_rules_target': json_file, 'match_count': len(matches)})

            for match in matches:
                data = {
                    'plist_file': plist_relative_path,
                    'plist_data': plist_data,
                    'yara_rule_file': match.namespace,
                    'yara_rule': match.rule,
                    'yara_rule_meta': match.meta,
                    'yara_rule_tags': match.tags,
                }
                event = Event(
                    datetime=self.sysdiagnose_creation_datetime,
                    message=f"Plist YARA rule '{match.rule}' from {match.namespace} matched in {plist_relative_path}",
                    module=self.module_name,
                    timestamp_desc='Sysdiagnose creation datetime',
                    data=data,
                )
                results.append(event.to_dict())

        return results

    @staticmethod
    def _load_json(json_file: str) -> dict | list | None:
        try:
            with open(json_file, 'r') as f:
                return json.load(f)
        except Exception:
            logger.exception(f"Error loading plist JSON {json_file}")
            return None
