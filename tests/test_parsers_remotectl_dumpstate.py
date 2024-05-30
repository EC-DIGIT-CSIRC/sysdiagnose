from parsers.remotectl_dumpstate import parse_path, get_log_files, parse_block
from tests import SysdiagnoseTestCase
import unittest


class TestParsersRemotectlDumpstate(SysdiagnoseTestCase):

    def test_get_remotectldumpstate(self):
        for log_root_path in self.log_root_paths:
            files = get_log_files(log_root_path)
            for file in files:
                print(f'Parsing {file}')
                parse_path(file)
                # just test for no exceptions

    def test_get_remotectldumpstate_2(self):
        lines = [
            'Local device',
            '	UUID: foo',
            '	Messaging Protocol Version: 3',
            '	Product Type: iPhone9,3',
            '	Properties: {',
            '		AppleInternal => false',
            '		CPUArchitecture => arm64',
            '	}',
            '	Services:',
            '		com.apple.remote.installcoordination_proxy',
            '		com.apple.bluetooth.BTPacketLogger.shim.remote',
            '',
            'Found foo',
            '	State: connected (connectable)',
            '	UUID: foo',
            '	Product Type: MacBookPro15,1',
            '	Messaging Protocol Version: 3',
            '	Heartbeat:',
            '		0 heartbeats sent, 0 received',
            '	Properties: {',
            '		AppleInternal => false',
            '		CPUArchitecture => x86_64h',
            '	}',
            '	Services:',
            '		com.apple.osanalytics.logRelay',
            '			Properties: {',
            '				UsesRemoteXPC => true',
            '			}',
            '		ssh',
            '			Properties: {',
            '				Legacy => true',
            '			}',
            '	Local Services:',
            '		com.apple.fusion.remote.service',
            '		com.apple.mobile.insecure_notification_proxy.shim.remote',
            '		com.apple.sysdiagnose.remote'
        ]
        expected_result = {
            "Local device": {
                "UUID": "foo",
                "Messaging Protocol Version": "3",
                "Product Type": "iPhone9,3",
                "Properties": {
                    "AppleInternal": "false",
                    "CPUArchitecture": "arm64"
                },
                "Services": [
                    "com.apple.remote.installcoordination_proxy",
                    "com.apple.bluetooth.BTPacketLogger.shim.remote"
                ]
            },
            "Found foo": {
                "State": "connected (connectable)",
                "UUID": "foo",
                "Product Type": "MacBookPro15,1",
                "Messaging Protocol Version": "3",
                "Heartbeat": [
                    "0 heartbeats sent, 0 received"
                ],
                "Properties": {
                    "AppleInternal": "false",
                    "CPUArchitecture": "x86_64h"
                },
                "Services": {
                    "com.apple.osanalytics.logRelay": {
                        "Properties": {
                            "UsesRemoteXPC": "true"
                        }
                    },
                    "ssh": {
                        "Properties": {
                            "Legacy": "true"
                        }
                    }
                },
                "Local Services": [
                    "com.apple.fusion.remote.service",
                    "com.apple.mobile.insecure_notification_proxy.shim.remote",
                    "com.apple.sysdiagnose.remote"
                ]
            }
        }
        result = parse_block(lines)
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()
