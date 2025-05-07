from sysdiagnose.utils.base import BaseAnalyserInterface
from sysdiagnose.parsers.mcstate_shared_profile import McStateSharedProfileParser
from sysdiagnose.utils import misc
import csv


# Temmporary analyser - for testing
class MCStateSharedProfileAnalyser(BaseAnalyserInterface):
    description = "Exports MCState Shared Profile stub files to CSV for better analysis"
    format = "csv"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def execute(self):
        result = []
        mcstatesharedprofile = McStateSharedProfileParser(self.config, self.case_id)
        mcstate_result = mcstatesharedprofile.get_result()

        for entry in mcstate_result:
            for key in ['SignerCerts', 'datetime', 'timestamp']:
                entry.pop(key, None)

            payload_contents = entry.pop('PayloadContent', None)

            entry_tpl = misc.flatten_dict(entry)

            for payload_content in payload_contents:
                item = entry_tpl.copy()
                item.update(misc.flatten_dict({'PayloadContent': payload_content}))
                result.append(item)

        return result

    def save_result(self, force: bool = False, indent=None):
        """
        Saves the result of the parsing operation to a file.

        Args:
            force (bool, optional): If True, forces the parsing operation even if the output cache or file exists. Defaults to False.
        """
        # save to file

        result = self.get_result(force)
        result_keys = set()
        for entry in result:
            result_keys.update(entry.keys())

        with open(self.output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(result_keys))
            writer.writeheader()
            writer.writerows(result)
