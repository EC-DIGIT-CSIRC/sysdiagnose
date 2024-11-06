from tests import SysdiagnoseTestCase
from sysdiagnose.utils import tabbasedhierarchy
import unittest


class TestTabbasedhierarchy(SysdiagnoseTestCase):

    def test_remotectldumpstateblock(self):
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
            '	Product Type: "MacBookPro15,1"',
            '	Messaging Protocol Version: 3',
            '	Heartbeat:',
            '		0 heartbeats sent, 0 received',
            '	Properties: {',
            '		AppleInternal => false',
            '		CPUArchitecture => x86_64h',
            '		EncryptedRemoteXPCPopulatedOIDs => [<capacity = 2>',
            '			0: 1.2.840.113635.100.6.83',
            '			1: 1.2.840.113635.100.6.84',
            '		]',
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
                    "CPUArchitecture": "x86_64h",
                    "EncryptedRemoteXPCPopulatedOIDs": {
                        "0": "1.2.840.113635.100.6.83",
                        "1": "1.2.840.113635.100.6.84"
                    }
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
        result = tabbasedhierarchy.parse_block(lines)
        self.maxDiff = None
        self.assertDictEqual(expected_result, result)

    def test_taskinfo_processblock(self):
        lines = ['\n', 'process: "launchd" [1] [unique ID: 1]\n', 'architecture: arm64\n', 'coalition (type 0) ID: 1\n', 'coalition (type 1) ID: 3\n', 'suspend count: 0\n', 'virtual bytes: 389.03 GB; phys_footprint bytes: 12.23 MB; phys_footprint lifetime maximum bytes: 12.36 MB\n', 'run time: 216 s\n', 'user/system time    (current threads): 0.145469 s / 0.000000 s\n', 'user/system time (terminated threads): 2.225133 s / 0.000000 s\n', 'P-time: 0.000000 s (0%)\n', 'P/E switches: 0\n', 'energy used (nJ): 0\n', 'interrupt wakeups: 21 (15 / 71.43% from platform idle)\n', 'default sched policy: POLICY_TIMESHARE\n', 'CPU usage monitor: none\n', 'CPU wakes monitor: 150 wakes per second (over system-default time period)\n', 'dirty tracking: untracked  dirty\n', 'boosts: 0 (0 externalized)\n', 'requested policy\n', '\treq apptype: TASK_APPTYPE_NONE\n', '\treq role: TASK_UNSPECIFIED (PRIO_DARWIN_ROLE_DEFAULT)\n', '\treq qos clamp: THREAD_QOS_UNSPECIFIED\n', '\treq base/override latency qos: LATENCY_QOS_TIER_UNSPECIFIED / LATENCY_QOS_TIER_UNSPECIFIED\n', '\treq base/override thruput qos: THROUGHPUT_QOS_TIER_UNSPECIFIED / THROUGHPUT_QOS_TIER_UNSPECIFIED\n', '\treq darwin BG: NO  \n', '\treq internal/external iotier: THROTTLE_LEVEL_TIER0 (IMPORTANT) / THROTTLE_LEVEL_TIER0 (IMPORTANT)\n', '\treq darwin BG iotier: THROTTLE_LEVEL_TIER2 (UTILITY)\n', '\treq managed: NO\n', '\treq other: \n', '\treq suppression (App Nap) behaviors: \n', 'effective policy\n', '\teff role: TASK_UNSPECIFIED (PRIO_DARWIN_ROLE_DEFAULT)\n', '\teff latency qos: LATENCY_QOS_TIER_UNSPECIFIED\n', '\teff thruput qos: THROUGHPUT_QOS_TIER_UNSPECIFIED\n', '\teff darwin BG: NO\n', '\teff iotier: THROTTLE_LEVEL_TIER0 (IMPORTANT)\n', '\teff managed: NO\n', '\teff qos ceiling: THREAD_QOS_USER_INITIATED\n', '\teff qos clamp: THREAD_QOS_UNSPECIFIED\n', '\teff other: \n', 'ios-appledaemon: NO\n', 'ios-imppromotion: NO\n', 'ios-application: NO\n', 'imp_donor: NO\n', 'imp_receiver: NO\n', 'pid suspended: NO\n', 'adaptive daemon: NO (boosted: NO)\n', 'threads:\n']
        expected_result = {'process': '"launchd" [1] [unique ID: 1]', 'architecture': 'arm64', 'coalition (type 0) ID': '1', 'coalition (type 1) ID': '3', 'suspend count': '0', 'virtual bytes': '389.03 GB; phys_footprint bytes: 12.23 MB; phys_footprint lifetime maximum bytes: 12.36 MB', 'run time': '216 s', 'user/system time    (current threads)': '0.145469 s / 0.000000 s', 'user/system time (terminated threads)': '2.225133 s / 0.000000 s', 'P-time': '0.000000 s (0%)', 'P/E switches': '0', 'energy used (nJ)': '0', 'interrupt wakeups': '21 (15 / 71.43% from platform idle)', 'default sched policy': 'POLICY_TIMESHARE', 'CPU usage monitor': 'none', 'CPU wakes monitor': '150 wakes per second (over system-default time period)', 'dirty tracking': 'untracked  dirty', 'boosts': '0 (0 externalized)', 'requested policy': {'req apptype': 'TASK_APPTYPE_NONE', 'req role': 'TASK_UNSPECIFIED (PRIO_DARWIN_ROLE_DEFAULT)', 'req qos clamp': 'THREAD_QOS_UNSPECIFIED', 'req base/override latency qos': 'LATENCY_QOS_TIER_UNSPECIFIED / LATENCY_QOS_TIER_UNSPECIFIED', 'req base/override thruput qos': 'THROUGHPUT_QOS_TIER_UNSPECIFIED / THROUGHPUT_QOS_TIER_UNSPECIFIED', 'req darwin BG': 'NO', 'req internal/external iotier': 'THROTTLE_LEVEL_TIER0 (IMPORTANT) / THROTTLE_LEVEL_TIER0 (IMPORTANT)', 'req darwin BG iotier': 'THROTTLE_LEVEL_TIER2 (UTILITY)', 'req managed': 'NO', 'req other': '', 'req suppression (App Nap) behaviors': ''}, 'effective policy': {'eff role': 'TASK_UNSPECIFIED (PRIO_DARWIN_ROLE_DEFAULT)', 'eff latency qos': 'LATENCY_QOS_TIER_UNSPECIFIED', 'eff thruput qos': 'THROUGHPUT_QOS_TIER_UNSPECIFIED', 'eff darwin BG': 'NO', 'eff iotier': 'THROTTLE_LEVEL_TIER0 (IMPORTANT)', 'eff managed': 'NO', 'eff qos ceiling': 'THREAD_QOS_USER_INITIATED', 'eff qos clamp': 'THREAD_QOS_UNSPECIFIED', 'eff other': ''}, 'ios-appledaemon': 'NO', 'ios-imppromotion': 'NO', 'ios-application': 'NO', 'imp_donor': 'NO', 'imp_receiver': 'NO', 'pid suspended': 'NO', 'adaptive daemon': 'NO (boosted: NO)', 'threads': ''}
        result = tabbasedhierarchy.parse_block(lines)
        self.maxDiff = None
        self.assertDictEqual(expected_result, result)

    def test_taskinfo_threadblock(self):
        lines = ['\tthread ID: 0x338 / 824\n', '\tthread ID: 0x338 / 824\n', '\tuser/system time: 0.000353 s / 0.000000 s\n', '\tCPU usage (over last tick): 0%\n', '\tsched mode: timeshare\n', '\tpolicy: POLICY_TIMESHARE\n', '\t\ttimeshare max  priority: 63\n', '\t\ttimeshare base priority: 31\n', '\t\ttimeshare cur  priority: 31\n', '\t\ttimeshare depressed: NO, prio -1\n', '\trequested policy:\n', '\t\treq thread qos: THREAD_QOS_LEGACY, relprio: 0\n', '\t\treq workqueue/pthread overides:\n', '\t\t\treq legacy qos override: THREAD_QOS_UNSPECIFIED\n', '\t\t\treq workqueue qos override: THREAD_QOS_UNSPECIFIED\n', '\t\treq kernel overides:\n', '\t\t\treq kevent overrides: THREAD_QOS_UNSPECIFIED\n', '\t\t\treq workloop servicer override: THREAD_QOS_UNSPECIFIED\n', '\t\treq turnstiles sync promotion qos: THREAD_QOS_UNSPECIFIED, user promotion base pri: 0\n', '\t\treq latency qos: LATENCY_QOS_TIER_UNSPECIFIED\n', '\t\treq thruput qos: THROUGHPUT_QOS_TIER_UNSPECIFIED\n', '\t\treq darwin BG: NO  \n', '\t\treq internal/external iotier: THROTTLE_LEVEL_TIER0 (IMPORTANT) / THROTTLE_LEVEL_TIER0 (IMPORTANT)\n', '\t\treq other: \n', '\teffective policy:\n', '\t\teff thread qos: THREAD_QOS_LEGACY\n', '\t\teff thread qos relprio: 0\n', '\t\teff promotion qos: THREAD_QOS_LEGACY\n', '\t\teff latency qos: LATENCY_QOS_TIER_1\n', '\t\teff thruput qos: THROUGHPUT_QOS_TIER_1\n', '\t\teff darwin BG: NO\n', '\t\teff iotier: THROTTLE_LEVEL_TIER0 (IMPORTANT)\n', '\t\teff other: \n', '\trun state: TH_STATE_WAITING\n', '\tflags: TH_FLAGS_SWAPPED |  | \n', '\tsuspend count: 0\n', '\tsleep time: 0 s\n', '\timportance in task: 0\n', '\n']
        expected_result = {"thread ID": "0x338 / 824", "user/system time": "0.000353 s / 0.000000 s", "CPU usage (over last tick)": "0%", "sched mode": "timeshare", "policy POLICY_TIMESHARE": {"timeshare max  priority": "63", "timeshare base priority": "31", "timeshare cur  priority": "31", "timeshare depressed": "NO, prio -1"}, "requested policy": {"req thread qos": "THREAD_QOS_LEGACY, relprio: 0", "req workqueue/pthread overides": {"req legacy qos override": "THREAD_QOS_UNSPECIFIED", "req workqueue qos override": "THREAD_QOS_UNSPECIFIED"}, "req kernel overides": {"req kevent overrides": "THREAD_QOS_UNSPECIFIED", "req workloop servicer override": "THREAD_QOS_UNSPECIFIED"}, "req turnstiles sync promotion qos": "THREAD_QOS_UNSPECIFIED, user promotion base pri: 0", "req latency qos": "LATENCY_QOS_TIER_UNSPECIFIED", "req thruput qos": "THROUGHPUT_QOS_TIER_UNSPECIFIED", "req darwin BG": "NO", "req internal/external iotier": "THROTTLE_LEVEL_TIER0 (IMPORTANT) / THROTTLE_LEVEL_TIER0 (IMPORTANT)", "req other": ""}, "effective policy": {"eff thread qos": "THREAD_QOS_LEGACY", "eff thread qos relprio": "0", "eff promotion qos": "THREAD_QOS_LEGACY", "eff latency qos": "LATENCY_QOS_TIER_1", "eff thruput qos": "THROUGHPUT_QOS_TIER_1", "eff darwin BG": "NO", "eff iotier": "THROTTLE_LEVEL_TIER0 (IMPORTANT)", "eff other": ""}, "run state": "TH_STATE_WAITING", "flags": "TH_FLAGS_SWAPPED |  |", "suspend count": "0", "sleep time": "0 s", "importance in task": "0"}
        result = tabbasedhierarchy.parse_block(lines)
        self.maxDiff = None
        self.assertDictEqual(expected_result, result)


if __name__ == '__main__':
    unittest.main()
