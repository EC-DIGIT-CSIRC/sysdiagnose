from sysdiagnose.utils.base import BaseAnalyserInterface, logger
from sysdiagnose.parsers.mcstate_shared_profile import McStateSharedProfileParser
import csv

# Temmporary analyser - for testing
class MCStateSharedProfile(BaseAnalyserInterface):
    description = "Test parser - 2025-04-09"
    format = "csv"  # by default json

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def possible_keys(self, mcstate_result):
        keys = []
        for payloadcontent in mcstate_result:
            payloadcontent_entry = mcstate_result[0]["PayloadContent"]
            for entry in payloadcontent_entry:
                keys = keys + list(entry.keys())

        # Remove duplicates
        keys = list(set(keys))

        return keys

    def execute(self):
        result = []
        mcstatesharedprofile = McStateSharedProfileParser(self.config, self.case_id)
        mcstate_result = mcstatesharedprofile.get_result(mcstatesharedprofile)

        # get all possible keys
        keys = self.possible_keys(mcstate_result)

        try:
            for payloadcontent in mcstate_result:
                payloadcontent_entry = mcstate_result[0]["PayloadContent"]
                for entry in payloadcontent_entry:
                    row = {}
                    for key in keys:
                        if key in entry.keys():
                            row[key] = entry[key]
                    result.append(row)
        except KeyError:
            result.append("Issue extracting trusted certificates")
            pass

        with open('mcstate_shared_profile.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=keys)
            writer.writeheader()
            writer.writerows(result)

        return str(result)
