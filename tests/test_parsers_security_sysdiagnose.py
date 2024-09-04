from parsers.security_sysdiagnose import SecuritySysdiagnoseParser
from tests import SysdiagnoseTestCase
import unittest
import os


class TestParsersSecuritySysdiagnose(SysdiagnoseTestCase):

    def test_get_security_sysdiagnose(self):
        for case_id, case in self.sd.cases().items():
            p = SecuritySysdiagnoseParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertEqual(len(files), 1)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

            result = p.get_result()
            if result:
                # test for no errors
                self.assertEqual(result.get('errors'), [])

    def test_process_buffer_keychain_state(self):
        input = [
            'Rapport keychain state:',
            'rapport: accc=<SecAccessControlRef: ck>,acct=69AAAFE9-A7FA-4BF3-922E-A14C33F11924,agrp=com.apple.rapport,cdat=2023-05-24 19:56:14 +0000,gena={length = 33, bytes = 0xe3456d6f 64656c49 6950686f 6e65392c ... 6973696f 6e494409 },invi=1,labl=iPhone,mdat=2023-05-24 19:56:14 +0000,musr={length = 0, bytes = 0x},pdmn=ck,sha1={length = 20, bytes = 0x1490ff273a003ef4089c46beb3731eb04754c7e5},svce=RPIdentity-SameAccountDevice,sync=1,tomb=0,vwht=Home',
        ]
        expected_output = {
            'rapport': [
                {'accc': '<SecAccessControlRef: ck>', 'acct': '69AAAFE9-A7FA-4BF3-922E-A14C33F11924', 'agrp': 'com.apple.rapport', 'cdat': '2023-05-24 19:56:14 +0000', 'gena': '{length = 33, bytes = 0xe3456d6f 64656c49 6950686f 6e65392c ... 6973696f 6e494409 }', 'invi': '1', 'labl': 'iPhone', 'mdat': '2023-05-24 19:56:14 +0000', 'musr': '{length = 0, bytes = 0x}', 'pdmn': 'ck', 'sha1': '{length = 20, bytes = 0x1490ff273a003ef4089c46beb3731eb04754c7e5}', 'svce': 'RPIdentity-SameAccountDevice', 'sync': '1', 'tomb': '0', 'vwht': 'Home'}
            ]
        }
        result = {}
        SecuritySysdiagnoseParser.process_buffer_keychain_state(input, result)
        self.maxDiff = None
        self.assertDictEqual(result, expected_output)

    def test_process_buffer_client(self):
        input = [
            'Client: trust',
            '2023-05-24 19:55:51 +0000 EventSoftFailure: OTAPKIEvent - Attributes: {product : iPhone OS, build : 19H349, errorDomain : NSOSStatusErrorDomain, modelid : iPhone9,3, errorCode : -67694 }',
            '2023-05-24 19:57:58 +0000 EventSoftFailure: MitmDetectionEvent - Attributes: {product : iPhone OS, build : 19H349, overallScore : 0, timeSinceLastReset : 127, rootUsages : (',
            ' foo, bar ',
            '), errorDomain : MITMErrorDomain, modelid : iPhone9,3, errorCode : 0 }'
        ]
        expected_output = {
            'client_trust': [
                {'date': '2023-05-24 19:55:51 +0000', 'result': 'EventSoftFailure', 'type': 'OTAPKIEvent', 'attributes': {'product': 'iPhone OS', 'build': '19H349', 'errorDomain': 'NSOSStatusErrorDomain', 'modelid': 'iPhone9,3', 'errorCode': '-67694'}},
                {'date': '2023-05-24 19:57:58 +0000', 'result': 'EventSoftFailure', 'type': 'MitmDetectionEvent', 'attributes': {'product': 'iPhone OS', 'build': '19H349', 'overallScore': '0', 'timeSinceLastReset': '127', 'rootUsages': '( foo, bar )', 'errorDomain': 'MITMErrorDomain', 'modelid': 'iPhone9,3', 'errorCode': '0'}}
            ]
        }
        result = {}
        SecuritySysdiagnoseParser.process_buffer_client(input, result)
        self.maxDiff = None
        self.assertDictEqual(result, expected_output)

    def test_process_buffer_keys_and_values(self):
        input = [
            'values',
            '~PCS-Notes-tomb: <CFData 0x8f9055600 [0x1fd49b730]>{length = 7741, capacity = 7741, bytes = 0x30821e39314c300e0c0a4170706c6963 ... 8df3270d7d823100}'
        ]
        expected_output = {
            'values': {
                '~PCS-Notes-tomb': '<CFData 0x8f9055600 [0x1fd49b730]>{length = 7741, capacity = 7741, bytes = 0x30821e39314c300e0c0a4170706c6963 ... 8df3270d7d823100}'
            }
        }
        result = {}
        SecuritySysdiagnoseParser.process_buffer_keys_and_values(input, result)
        self.maxDiff = None
        self.assertDictEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()