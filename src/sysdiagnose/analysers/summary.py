from sysdiagnose.utils.base import BaseAnalyserInterface, logger
from sysdiagnose.parsers.remotectl_dumpstate import RemotectlDumpstateParser
from sysdiagnose.parsers.security_sysdiagnose import SecuritySysdiagnoseParser
from sysdiagnose.parsers.transparency_json import TransparencyJsonParser
from sysdiagnose.parsers.plists import PlistParser
import os


class SummaryAnalyser(BaseAnalyserInterface):
    description = "Gives some summary info from the device"
    format = "txt"  # by default json

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def execute(self):
        result = []

        rctl_parser = RemotectlDumpstateParser(self.config, self.case_id)
        rctl_result = rctl_parser.get_result()
        # current device info
        try:
            result.append("## Device Info:")
            rctl_result['Local device']['Properties']['SerialNumber']
            rctl_result['Local device']['Properties']['UniqueDeviceID']
            rctl_result['Local device']['Properties']['OSVersion']
        except KeyError:
            result.append("Issue extracting device info")
            pass

        trans_parser = TransparencyJsonParser(self.config, self.case_id)
        trans_result = trans_parser.get_result()
        # extract email addresses / account info
        result.append("\n## Accounts")
        try:
            for account, val in trans_result['stateMachine']['selfVerification']['server'].items():
                result.append(f"- {account}")
        except KeyError:
            # result.append("Issue extracting stateMachine selfVerification account info")
            pass

        plist_parser = PlistParser(self.config, self.case_id)
        mobilecal_result = plist_parser.parse_file(os.path.join(plist_parser.case_data_subfolder, 'logs/CalendarPreferences/com.apple.mobilecal.plist'))
        try:
            for owner in mobilecal_result['OwnerEmailAddress']:
                result.append(f"- {owner}")
        except KeyError:
            # result.append("Issue extracting mobilecal owner email")
            pass

        # extract known devices
        try:
            result.append("\n## Known Devices")
            for key, device in trans_result['stateMachine']['devices'].items():
                result.append(f"Name: {device['name']}")
                result.append(f"Model: {device['model']}")
                result.append(f"OS: {device['osVersion']}")
        except KeyError:
            result.append("Issue extracting known devices")
            pass

        sec_parser = SecuritySysdiagnoseParser(self.config, self.case_id)
        sec_result = sec_parser.get_result()
        if 'errors' in sec_result and len(sec_result['errors']) > 0:
            pass
        else:
            # use metadata section
            for item in sec_result:
                if item['section'] == 'metadata' and 'circle' in item:
                    result.append("\n## Circle")
                    result.extend(item['circle'])

        logger.warning(
            "This is a work in progress. The output may not be complete or accurate."
        )
        # TODO list configuration profiles
        # TODO extract even more, ideally from plist/json and not jsonl
        # TODO also write the unit test

        print("\n".join(result))
        return "\n".join(result)
