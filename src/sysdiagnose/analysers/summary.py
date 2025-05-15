from sysdiagnose.analysers import plist
from sysdiagnose.utils.base import BaseAnalyserInterface, logger
from sysdiagnose.parsers.remotectl_dumpstate import RemotectlDumpstateParser
from sysdiagnose.parsers.security_sysdiagnose import SecuritySysdiagnoseParser
from sysdiagnose.parsers.transparency_json import TransparencyJsonParser
from sysdiagnose.parsers.mcstate_shared_profile import McStateSharedProfileParser
from sysdiagnose.parsers.plists import PlistParser
import os


class SummaryAnalyser(BaseAnalyserInterface):
    description = "Gives some summary info from the device"
    format = 'md'  # by default json

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def execute(self):
        result = []

        rctl_parser = RemotectlDumpstateParser(self.config, self.case_id)
        rctl_result = rctl_parser.get_result()
        # current device info
        try:
            result.append('## Device Info:')
            result.append(f"- Model: {rctl_result['Local device']['Product Type']}")
            result.append(f"- Version: {rctl_result['Local device']['OS Build']}")
            result.append(f"- Serial Number: {rctl_result['Local device']['Properties']['SerialNumber']}")
            result.append(f"- Unique Device ID: {rctl_result['Local device']['Properties']['UniqueDeviceID']}")
        except KeyError:
            result.append('Issue extracting device info')
            pass

        plist_parser = PlistParser(self.config, self.case_id)
        plist_result = plist_parser.parse_file(os.path.join(plist_parser.case_data_subfolder, 'logs', 'MCState', 'User', 'EffectiveUserSettings.plist'))
        try:
            result.append(f"- Lockdown mode: {plist_result['restrictedBool']['allowLockdownMode']['value']}")
        except KeyError:
            pass

        trans_parser = TransparencyJsonParser(self.config, self.case_id)
        trans_result = trans_parser.get_result()
        # extract email addresses / account info
        result.append('\n## Accounts')
        try:
            for account, val in trans_result['stateMachine']['selfVerification']['server'].items():
                result.append(f"- {account}")
        except KeyError:
            # result.append('Issue extracting stateMachine selfVerification account info')
            pass

        try:
            uris = trans_result['stateMachine']['lastValidateSelf']['diagnostics']['KTSelfVerificationInfo']['uris']
            for uri in uris:
                if uri.startswith('im://mailto:'):
                    result.append(f"- Owner's email: {uri[12:]}")
                if uri.startswith('im://tel:'):
                    result.append(f"- Owner's phone: {uri[9:]}")
        except KeyError:
            pass

        try:
            uris = trans_result['stateMachine']['cloudRecords']['optIn'].keys()
            for uri in uris:
                if uri.startswith('im://mailto:'):
                    result.append(f"- Owner's email: {uri[12:]}")
                if uri.startswith('im://tel:'):
                    result.append(f"- Owner's phone: {uri[9:]}")
        except KeyError:
            pass

        mobilecal_result = PlistParser.parse_file(os.path.join(self.case_data_subfolder, 'logs/CalendarPreferences/com.apple.mobilecal.plist'))
        try:
            for owner in mobilecal_result['OwnerEmailAddress']:
                result.append(f"- {owner}")
        except KeyError:
            # result.append('Issue extracting mobilecal owner email')
            pass

        # extract known devices
        try:
            result.append('\n## Known Devices')
            result.append("| Serial       | Model            | OS        | Name                 |")
            result.append("|--------------|------------------|-----------|----------------------|")
            for key, device in trans_result['stateMachine']['devices'].items():
                result.append(f"| {device['serial']} | {device['model']:16} | {device['osVersion']:9} | {device['name']:20} |")
                # result.append(f"Name: {device['name']}")
                # result.append(f"- Model: {device['model']}")
                # result.append(f"- OS: {device['osVersion']}")
                # result.append(f"- Serial: {device['serial']}")
        except KeyError:
            result.append('Issue extracting known devices')
            pass

        sec_parser = SecuritySysdiagnoseParser(self.config, self.case_id)
        sec_result = sec_parser.get_result()
        if 'errors' in sec_result and len(sec_result['errors']) > 0:
            pass
        else:
            # FIXME this code is not touched - use metadata section
            for item in sec_result:
                if item['section'] == 'metadata':
                    if 'circle' in item:
                        result.append('\n## Circle')
                        result.extend(item['circle'])

        mcstatesharedprofile_parser = McStateSharedProfileParser(self.config, self.case_id)
        mcstate_result = mcstatesharedprofile_parser.get_result()
        # Extract trusted certificates and configuration profiles
        # TODO fix the following piece of code, it is waaay too long and not readable
        #  - should return subjet which includes user account
        #  - should be cleaned a LOT and made more meaningful
        try:
            # the logic below needs to be reimplemented after understanding the data structure better.
            # store it in a temporary variable, sort it and give a better (sorted) output that makes sense
            result.append('\n## Trusted certificates and configuration profiles')
            for profile in mcstate_result:
                if 'InstallDate' in profile:
                    result.append(f"Install date {profile['InstallDate']}")

                if 'PayloadIdentifier' in profile:
                    result.append(f"Payload identifier: {profile['PayloadIdentifier']}")
                if 'PayloadOrganization' in profile:
                    result.append(f"Payload organisation: {profile['PayloadOrganization']}")
                if 'PayloadUUID' in profile:
                    result.append(f"Payload UUID: {profile['PayloadUUID']}")
                if 'ProfileWasEncrypted' in profile and not profile['ProfileWasEncrypted']:
                    result.append('Profile was NOT encrypted!')

                if 'InstallOptions' in profile:
                    if 'installedByMDM' in profile['InstallOptions']:
                        result.append(f"Installed by MDM: {profile['InstallOptions']['installedByMDM']}")
                    if 'installedBy' in profile['InstallOptions']:
                        result.append(f"Installed by: {profile['InstallOptions']['installedBy']}")
                    if 'isOTAInstallation' in profile['InstallOptions']:
                        result.append(f"OTA installation: {profile['InstallOptions']['isOTAInstallation']}")
                    if 'managingProfileIdentifier' in profile['InstallOptions']:
                        result.append(f"Managing profile identifier: {profile['InstallOptions']['managingProfileIdentifier']}")

                if 'OTAProfileStub' in profile:
                    result.append('OTA Profile Stub:')
                    result.append(f"\tOrganisation: {profile['OTAProfileStub']['PayloadOrganization']}")
                    result.append(f"\tIdentifier: {profile['OTAProfileStub']['PayloadIdentifier']}")
                    result.append(f"\tDescription: {profile['OTAProfileStub']['PayloadDescription']}")
                    result.append(f"\tType: {profile['OTAProfileStub']['PayloadType']}")
                    result.append(f"\tURL: {profile['OTAProfileStub']['PayloadContent']['URL']}")
                    result.append(f"\tUUID: {profile['OTAProfileStub']['PayloadUUID']}")

                for key in profile.keys():
                    if 'URL' in key:
                        result.append(f"\t{key}: {profile[key]}")

                for payloadcontent_item in profile['PayloadContent']:
                    result.append('Payload content:')
                    if 'PayloadIdentifier' in payloadcontent_item:
                        result.append(f"\tIdentifier: {payloadcontent_item['PayloadIdentifier']}")
                    if 'PayloadDescription' in payloadcontent_item:
                        result.append(f"\tDescription: {payloadcontent_item['PayloadDescription']}")
                    if 'PayloadDisplayName' in payloadcontent_item:
                        result.append(f"\tDisplay name: {payloadcontent_item['PayloadDisplayName']}")

                    if 'CertSubject' in payloadcontent_item:
                        result.append(f"\tSubject: {payloadcontent_item['CertSubject']}")
                    if 'PayloadType' in payloadcontent_item:
                        result.append(f"\tType: {payloadcontent_item['PayloadType']}")
                    # if 'ServerURL' in payloadcontent_item:
                    #     result.append(f"\tURL: {payloadcontent_item['ServerURL']}")

                    for key in payloadcontent_item.keys():
                        if 'URL' in key:
                            result.append(f"\t{key}: {payloadcontent_item[key]}")

                    result.append('')

                result.append('----------------------')
        except (KeyError, IndexError):
            result.append('No McStateShared Profiles, or issue extracting trusted certificates and profiles.')
            pass

        # TODO extract even more, ideally from plist/json and not jsonl
        # TODO also write the unit test

        print("\n".join(result))
        return "\n".join(result)
