from tests import SysdiagnoseTestCase
from sysdiagnose.utils import multilinelog
import unittest


class TestMultiline(SysdiagnoseTestCase):

    def test_multilinelog_plist(self):
        s = '''Wed May 24 12:58:04 2023 [173] <debug> (0x16bf9b000) MA: -[MobileActivationDaemon handleActivationInfoWithSession:activationSignature:completionBlock:]: Activation message:
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
<key>AccountToken</key>
<data>
dGVzdA==
</data>
<key>AccountTokenCertificate</key>
<data>
dGVzdA==
</data>
<key>unbrick</key>
<true/>
</dict>
</plist>

'''
        expected_result = {
            'timestamp': 1684933084.0,
            'datetime': '2023-05-24T12:58:04.000000+00:00',
            'loglevel': 'debug',
            'hexID': '0x16bf9b000',
            'event_type': 'MobileActivationDaemon handleActivationInfoWithSession:activationSignature:completionBlock:',
            'msg': 'Activation message:',
            'plist': {'AccountToken': 'test', 'AccountTokenCertificate': 'test', 'unbrick': True}}
        result = multilinelog.extract_from_string(s)
        self.assertDictEqual(expected_result, result[0])

        pass

    def test_multilinelog_curlybrackets(self):
        # LATER parse the bracket as json, but it's a though job:
        # - find the first bracket, then the last bracket by counting up and down again, extract the inside.
        # - but if the inside is not at the end, the rest of the text still needs to be added somewhere... So not sure what is the best.
        s = '''Wed May 24 13:05:36 2023 [72] <err> (0x16be43000) +[MCMMetadata readAndValidateMetadataAtFileUrl:forUserIdentity:containerClass:checkClassPath:transient:error:]: 199: Failed to validate metadata at URL [file:///private/var/mobile/Containers/Data/Application/0984009B-81D1-4F7F-BDBD-261E22059155/.com.apple.mobile_container_manager.metadata.plist]: {
    MCMMetadataActiveDPClass = 0;
    MCMMetadataContentClass = 2;
    MCMMetadataIdentifier = "com.apple.VoiceMemos";
    MCMMetadataInfo =     {
        "com.apple.MobileInstallation.ContentProtectionClass" = 0;
    };
    MCMMetadataSchemaVersion = 1;
    MCMMetadataUUID = "12036663-1F3A-45B3-A34C-402D5BB7D4FB";
    MCMMetadataUserIdentity =     {
        personaUniqueString = "83CB8039-725D-4462-84C2-7F79F0A6EFB3";
        posixGID = 501;
        posixUID = 501;
        type = 0;
        version = 2;
    };
    MCMMetadataVersion = 6;
} (Error Domain=MCMErrorDomain Code=29 "Invalid metadata-URLs should match: /private/var/mobile/Containers/Data/Application/0984009B-81D1-4F7F-BDBD-261E22059155 : /private/var/mobile/Containers/Data/VPNPlugin/0984009B-81D1-4F7F-BDBD-261E22059155" UserInfo={SourceFileLine=370, NSLocalizedDescription=Invalid metadata-URLs should match: /private/var/mobile/Containers/Data/Application/0984009B-81D1-4F7F-BDBD-261E22059155 : /private/var/mobile/Containers/Data/VPNPlugin/0984009B-81D1-4F7F-BDBD-261E22059155, FunctionName=+[MCMMetadata _readAndValidateMetadataInDictionary:containerURL:forUserIdentity:containerClass:checkClassPath:fsNode:transient:error:]})
'''
        expected_result = {
            'timestamp': 1684933536.0,
            'datetime': '2023-05-24T13:05:36.000000+00:00',
            'loglevel': 'err',
            'hexID': '0x16be43000',
            'msg': '+[MCMMetadata readAndValidateMetadataAtFileUrl:forUserIdentity:containerClass:checkClassPath:transient:error:]: 199: Failed to validate metadata at URL [file:///private/var/mobile/Containers/Data/Application/0984009B-81D1-4F7F-BDBD-261E22059155/.com.apple.mobile_container_manager.metadata.plist]: {\n    MCMMetadataActiveDPClass = 0;\n    MCMMetadataContentClass = 2;\n    MCMMetadataIdentifier = "com.apple.VoiceMemos";\n    MCMMetadataInfo =     {\n        "com.apple.MobileInstallation.ContentProtectionClass" = 0;\n    };\n    MCMMetadataSchemaVersion = 1;\n    MCMMetadataUUID = "12036663-1F3A-45B3-A34C-402D5BB7D4FB";\n    MCMMetadataUserIdentity =     {\n        personaUniqueString = "83CB8039-725D-4462-84C2-7F79F0A6EFB3";\n        posixGID = 501;\n        posixUID = 501;\n        type = 0;\n        version = 2;\n    };\n    MCMMetadataVersion = 6;\n} (Error Domain=MCMErrorDomain Code=29 "Invalid metadata-URLs should match: /private/var/mobile/Containers/Data/Application/0984009B-81D1-4F7F-BDBD-261E22059155 : /private/var/mobile/Containers/Data/VPNPlugin/0984009B-81D1-4F7F-BDBD-261E22059155" UserInfo={SourceFileLine=370, NSLocalizedDescription=Invalid metadata-URLs should match: /private/var/mobile/Containers/Data/Application/0984009B-81D1-4F7F-BDBD-261E22059155 : /private/var/mobile/Containers/Data/VPNPlugin/0984009B-81D1-4F7F-BDBD-261E22059155, FunctionName=+[MCMMetadata _readAndValidateMetadataInDictionary:containerURL:forUserIdentity:containerClass:checkClassPath:fsNode:transient:error:]})'}
        result = multilinelog.extract_from_string(s)
        self.assertDictEqual(expected_result, result[0])

    def test_multilinelog_simple_1(self):
        s = '''Wed May 24 12:55:37 2023 [72] <notice> (0x16afb3000) -[MCMClientConnection _regenerateAllSystemContainerPaths]: Rolling system container directory UUIDs on disk'''
        expected_result = {
            'timestamp': 1684932937.0,
            'datetime': '2023-05-24T12:55:37.000000+00:00',
            'loglevel': 'notice',
            'hexID': '0x16afb3000',
            'event_type': 'MCMClientConnection _regenerateAllSystemContainerPaths',
            'msg': 'Rolling system container directory UUIDs on disk'}
        result = multilinelog.extract_from_string(s)
        self.assertDictEqual(expected_result, result[0])

    def test_mutlinelog_simple_2(self):
        s = '''Wed May 24 13:05:30 2023 [72] <notice> (0x16be43000) _containermanagerd_init_block_invoke: containermanagerd first boot cleanup complete'''
        expected_result = {
            'timestamp': 1684933530.0,
            'datetime': '2023-05-24T13:05:30.000000+00:00',
            'loglevel': 'notice',
            'hexID': '0x16be43000',
            'msg': '_containermanagerd_init_block_invoke: containermanagerd first boot cleanup complete'}
        result = multilinelog.extract_from_string(s)
        self.assertDictEqual(expected_result, result[0])

    def test_multilinelog_simple_multiplelines(self):
        s = '''Wed May 24 13:05:30 2023 [72] <notice> (0x16be43000) _containermanagerd_init_block_invoke: containermanagerd first boot cleanup complete
Wed May 24 12:55:37 2023 [72] <notice> (0x16afb3000) -[MCMClientConnection _regenerateAllSystemContainerPaths]: Rolling system container directory UUIDs on disk'''
        expected_result_0 = {
            'timestamp': 1684933530.0,
            'datetime': '2023-05-24T13:05:30.000000+00:00',
            'loglevel': 'notice',
            'hexID': '0x16be43000',
            'msg': '_containermanagerd_init_block_invoke: containermanagerd first boot cleanup complete'}
        expected_result_1 = {
            'timestamp': 1684932937.0,
            'datetime': '2023-05-24T12:55:37.000000+00:00',
            'loglevel': 'notice',
            'hexID': '0x16afb3000',
            'event_type': 'MCMClientConnection _regenerateAllSystemContainerPaths',
            'msg': 'Rolling system container directory UUIDs on disk'}
        result = multilinelog.extract_from_string(s)
        self.assertDictEqual(expected_result_0, result[0])
        self.assertDictEqual(expected_result_1, result[1])

    def test_mutilinelog_emptylines(self):
        s = '''\n\n'''
        result = multilinelog.extract_from_string(s)
        self.assertEqual(0, len(result))

    def test_multilinelog_keyvalue(self):
        s = '''Wed May 24 12:55:37 2023 [72] <notice> (0x16afb3000) -[MCMClientConnection _regenerateAllSystemContainerPaths]: Rolling system container directory UUIDs on disk
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: ____________________ Mobile Activation Startup _____________________
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: build_version: 19H349
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: internal_build: false
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: uid: 501
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: user_name: mobile
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: system_container_path: /private/var/containers/Data/System/4E023926-12C3-401D-BE00-06FC33B50889
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: regulatory_images_path: /private/var/containers/Shared/SystemGroup/AF534A77-07C2-4140-917E-BEE330B5B1AF
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: hardware_model: D101AP
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: product_type: iPhone9,3
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: device_class: iPhone
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: has_telephony: true
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: should_hactivate: false
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: is_fpga: false
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: is_devfused_undemoted: false
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: is_prodfused_demoted: false
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: soc_generation: H9
Wed May 24 13:08:13 2023 [135] <debug> (0x16f1db000) MA: main: ____________________________________________________________________'''
        expected_result_0 = {
            'timestamp': 1684932937.0,
            'datetime': '2023-05-24T12:55:37.000000+00:00',
            'loglevel': 'notice',
            'hexID': '0x16afb3000',
            'event_type': 'MCMClientConnection _regenerateAllSystemContainerPaths',
            'msg': 'Rolling system container directory UUIDs on disk'}
        expected_result_1 = {
            'timestamp': 1684933693.0,
            'datetime': '2023-05-24T13:08:13.000000+00:00',
            'loglevel': 'debug',
            'hexID': '0x16f1db000',
            'msg': 'MA: main: ____________________ Mobile Activation Startup _____________________',
            'build_version': '19H349',
            'internal_build': 'false',
            'uid': '501',
            'user_name': 'mobile',
            'system_container_path': '/private/var/containers/Data/System/4E023926-12C3-401D-BE00-06FC33B50889',
            'regulatory_images_path': '/private/var/containers/Shared/SystemGroup/AF534A77-07C2-4140-917E-BEE330B5B1AF',
            'hardware_model': 'D101AP',
            'product_type': 'iPhone9,3',
            'device_class': 'iPhone',
            'has_telephony': 'true',
            'should_hactivate': 'false',
            'is_fpga': 'false',
            'is_devfused_undemoted': 'false',
            'is_prodfused_demoted': 'false',
            'soc_generation': 'H9'}
        result = multilinelog.extract_from_string(s)
        self.assertDictEqual(expected_result_0, result[0])
        self.assertDictEqual(expected_result_1, result[1])

    def test_multilinelog_keyvalue_onlyend(self):
        s = '''Sat Feb 18 09:48:38 2023 [2695] <debug> (0x16dc37000) MA: main: ____________________________________________________________________
Sat Feb 18 09:48:39 2023 [2695] <debug> (0x16dc37000) MA: dealwith_activation: Activation State: Activated'''
        expected_result_0 = {
            'timestamp': 1676713718.0,
            'datetime': '2023-02-18T09:48:38.000000+00:00',
            'loglevel': 'debug',
            'hexID': '0x16dc37000',
            'msg': 'MA: main: ____________________________________________________________________'}
        expected_result_1 = {
            'timestamp': 1676713719.0,
            'datetime': '2023-02-18T09:48:39.000000+00:00',
            'loglevel': 'debug',
            'hexID': '0x16dc37000',
            'msg': 'MA: dealwith_activation: Activation State: Activated'}
        result = multilinelog.extract_from_string(s)
        self.assertDictEqual(expected_result_0, result[0])
        self.assertDictEqual(expected_result_1, result[1])

    def test_multilinelog_keyvalue_onlystart(self):
        s = '''Fri Dec  2 11:32:19 2022 [84816] <debug> (0x16afff000) MA: main: ____________________ Mobile Activation Startup _____________________'''
        expected_result = {
            'timestamp': 1669980739.0,
            'datetime': '2022-12-02T11:32:19.000000+00:00',
            'loglevel': 'debug',
            'hexID': '0x16afff000',
            'msg': 'MA: main: ____________________ Mobile Activation Startup _____________________'}
        result = multilinelog.extract_from_string(s)
        self.assertDictEqual(expected_result, result[0])


if __name__ == '__main__':
    unittest.main()
