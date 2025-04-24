from sysdiagnose.utils.base import BaseAnalyserInterface, logger
from sysdiagnose.parsers.remotectl_dumpstate import RemotectlDumpstateParser
from sysdiagnose.parsers.security_sysdiagnose import SecuritySysdiagnoseParser
from sysdiagnose.parsers.transparency_json import TransparencyJsonParser
from sysdiagnose.parsers.mcstate_shared_profile import McStateSharedProfileParser
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

        try:
            uris = trans_result["stateMachine"]["lastValidateSelf"]["diagnostics"]["KTSelfVerificationInfo"]["uris"]
            for uri in uris:
                if uri.startswith("im://mailto:"):
                    result.append(f"Owner's email: {uri[12:]}")
                if uri.startswith("im://tel:"):
                    result.append(f"Owner's phone: {uri[9:]}")
        except KeyError:
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
                result.append(f"Serial: {device['serial']}")
                result.append("----------------")
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

        # Extract trusted certificates and configuration profiles
        # TODO fix the following piece of code
        #  - should return subjet which includes user account
        #  - should be cleaned a bit and made more meaningful
        mcstatesharedprofile = McStateSharedProfileParser(self.config, self.case_id)
        mcstate_result = mcstatesharedprofile.get_result()
        # try:
        #     result.append("\n## Trusted certificates")
        #     for payloadcontent in mcstate_result:
        #         payloadcontent_entry = mcstate_result[0]["PayloadContent"]
        #         for entry in payloadcontent_entry:
        #             if("PayloadIdentifier" in entry.keys()):
        #                 result.append("Identifier: %s" % entry["PayloadIdentifier"])
        #             if("PayloadDescription" in entry.keys()):
        #                 result.append("Description: %s" % entry["PayloadDescription"])
        #             if("PayloadDisplayName" in entry.keys()):
        #                 result.append("Display name: %s" % entry["PayloadDisplayName"])
        #             if("InstallDate" in entry.keys()):
        #                 result.append("Install date %s" % entry["InstallDate"])
        #             if("CertSubject" in entry.keys()):
        #                 result.append("Subject: %s" % entry["CertSubject"])
        #             if("PayloadType" in entry.keys()):
        #                 result.append("Type: %s" % entry["PayloadType"])
        #             if("ServerURL" in entry.keys()):
        #                 result.append("URL: %s" % entry["ServerURL"])
        #             if("OTAProfileStub" in entry.keys()):
        #                 url  = entry["OTAProfileStub"]["PayloadContent"]["URL"]
        #                 identifier = entry["OTAProfileStub"]["PayloadIdentifier"]
        #                 description = entry["OTAProfileStub"]["PayloadDescription"]
        #                 type = entry["OTAProfileStub"]["PayloadType"]
        #                 uuid = entry["OTAProfileStub"]["PayloadUUID"]
        #                 org = entry["OTAProfileStub"]["PayloadOrganization"]
        #                 result.append("\tOrganisation: %s" % org)
        #                 result.append("\tIdentifier: %s" % identifier)
        #                 result.append("\tDescription: %s" % description)
        #                 result.append("\tType: %s" % type)
        #                 result.append("\tURL: %s" % url)
        #                 result.append("\tUUID: %s" % uuid)
        #             result.append("----------------------")
        # except KeyError:
        #     result.append("Issue extracting trusted certificates")
        #     pass

        # TODO ensure the following piece of code is complete and exhaustive
        result.append("\n## Configuration Profiles")
        try:
            if "PayloadIdentifier" in mcstate_result[0].keys():
                result.append("Identifier %s" % mcstate_result[0]["PayloadIdentifier"])
            if "PayloadDescription" in mcstate_result[0].keys():
                result.append("Desription %s" % mcstate_result[0]["PayloadDescription"])
            if "InstallDate" in mcstate_result[0].keys():
                result.append("Install date %s" % mcstate_result[0]["InstallDate"])
            if "OTAProfileStub" in mcstate_result[0].keys():
                url = mcstate_result[0]["OTAProfileStub"]["PayloadContent"]["URL"]
                identifier = mcstate_result[0]["OTAProfileStub"]["PayloadIdentifier"]
                description = mcstate_result[0]["OTAProfileStub"]["PayloadDescription"]
                type = mcstate_result[0]["OTAProfileStub"]["PayloadType"]
                uuid = mcstate_result[0]["OTAProfileStub"]["PayloadUUID"]
                org = mcstate_result[0]["OTAProfileStub"]["PayloadOrganization"]
                result.append("\tOrganisation: %s" % org)
                result.append("\tIdentifier: %s" % identifier)
                result.append("\tDescription: %s" % description)
                result.append("\tType: %s" % type)
                result.append("\tURL: %s" % url)
                result.append("\tUUID: %s" % uuid)
                result.append("----------------------")
        except KeyError:
            result.append("Issue extracting configuration profiles")
            pass

        logger.warning(
            "This is a work in progress. The output may not be complete or accurate."
        )

        # TODO extract even more, ideally from plist/json and not jsonl
        # TODO also write the unit test

        print("\n".join(result))
        return "\n".join(result)
