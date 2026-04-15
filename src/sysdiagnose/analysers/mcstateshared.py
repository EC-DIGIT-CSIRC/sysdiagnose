import csv

from sysdiagnose.parsers.mcstate_shared_profile import McStateSharedProfileParser
from sysdiagnose.utils import misc
from sysdiagnose.utils.base import BaseAnalyserInterface, SysdiagnoseConfig


# Temmporary analyser - for testing
class MCStateSharedProfileAnalyser(BaseAnalyserInterface):
    description = "Exports MCState Shared Profile stub files to CSV for better analysis."
    format = "csv"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def execute(self):
        result = []
        mcstatesharedprofile = McStateSharedProfileParser(self.config, self.case_id)
        mcstate_result = mcstatesharedprofile.get_result()

        for entry in mcstate_result:
            for key in ['SignerCerts', 'datetime', 'timestamp']:
                entry['data'].pop(key, None)

            payload_contents = entry['data'].pop('PayloadContent', None)

            entry_tpl = misc.flatten_dict(entry['data'])

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
        if force or self._result is None or not self.output_exists():
            self._result = self.execute_with_result_summary()
        else:
            self._result_summary = self.load_result_summary()

        result_keys = set()
        for entry in self._result:
            result_keys.update(entry.keys())

        with open(self.output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(result_keys))
            writer.writeheader()
            writer.writerows(self._result)

        self.save_result_summary()
