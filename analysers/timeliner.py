#! /usr/bin/env python3

# For Python3
# Script to extract timestamp and generate a timesketch output
# Author: david@autopsit.org
#

from datetime import datetime, timezone
from parsers.logarchive import LogarchiveParser
from parsers.mobileactivation import MobileActivationParser
from parsers.powerlogs import PowerLogsParser
from parsers.swcutil import SwcutilParser
from parsers.accessibility_tcc import AccessibilityTccParser
from parsers.shutdownlogs import ShutdownLogsParser
from parsers.wifisecurity import WifiSecurityParser
from parsers.wifi_known_networks import WifiKnownNetworksParser
from parsers.crashlogs import CrashLogsParser
from collections.abc import Generator
from utils.base import BaseAnalyserInterface


class TimelinerAnalyser(BaseAnalyserInterface):
    description = 'Generate a Timesketch compatible timeline'
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    # Timesketch format:
    # https://timesketch.org/guides/user/import-from-json-csv/
    # Mandatory: timestamps must be in microseconds !!!
    # {"message": "A message","timestamp": 123456789,"datetime": "2015-07-24T19:01:01+00:00","timestamp_desc": "Write time","extra_field_1": "foo"}

    def a__extract_ts_mobileactivation(self) -> Generator[dict, None, None]:
        try:
            p = MobileActivationParser(self.config, self.case_id)
            data = p.get_result()
            for event in data:
                ts_event = {
                    'message': 'Mobile Activation',
                    'timestamp': event['timestamp'] * 1000000,
                    'datetime': event['datetime'],
                    'timestamp_desc': 'Mobile Activation Time'
                }
                try:
                    ts_event['extra_field_1'] = f"Build Version: {event['build_version']}"
                except KeyError:
                    # skip other type of event
                    # FIXME what should we do? the log file (now) contains nice timestamps, do we want to extract less, but summarized, data?
                    continue
                yield ts_event
        except Exception as e:
            print(f"ERROR while extracting timestamp from mobileactivation file. Reason: {str(e)}")

    def a__extract_ts_powerlogs(self) -> Generator[dict, None, None]:
        try:
            p = PowerLogsParser(self.config, self.case_id)
            data = p.get_result()
            # extract tables of interest
            for entry in TimelinerAnalyser.__powerlogs__PLProcessMonitorAgent_EventPoint_ProcessExit(data):
                yield entry
            for entry in TimelinerAnalyser.__powerlogs__PLProcessMonitorAgent_EventBackward_ProcessExitHistogram(data):
                yield entry
            for entry in TimelinerAnalyser.__powerlogs__PLAccountingOperator_EventNone_Nodes(data):
                yield entry
        except Exception as e:
            print(f"ERROR while extracting timestamp from powerlogs. Reason: {str(e)}")

    def a__extract_ts_swcutil(self) -> Generator[dict, None, None]:
        try:
            p = SwcutilParser(self.config, self.case_id)
            data = p.get_result()
            if 'db' in data.keys():
                for service in data['db']:
                    try:
                        timestamp = datetime.strptime(service['Last Checked'], '%Y-%m-%d %H:%M:%S %z')
                        ts_event = {
                            'message': service['Service'],
                            'timestamp': timestamp.timestamp() * 1000000,
                            'datetime': timestamp.isoformat(),
                            'timestamp_desc': 'swcutil last checkeed',
                            'extra_field_1': f"application: {service['App ID']}"
                        }
                        yield ts_event
                    except KeyError:
                        # some entries do not have a Last Checked or timestamp field
                        # print(f"WARNING {filename} while extracting timestamp from {(service['Service'])} - {(service['App ID'])}. Record not inserted.")
                        pass
        except Exception as e:
            print(f"ERROR while extracting timestamp from swcutil. Reason {str(e)}")

    def a__extract_ts_accessibility_tcc(self) -> Generator[dict, None, None]:
        try:
            p = AccessibilityTccParser(self.config, self.case_id)
            data = p.get_result()
            if 'access' in data.keys():
                for access in data['access']:
                    # create timeline entry
                    timestamp = datetime.fromtimestamp(access['last_modified'], tz=timezone.utc)
                    ts_event = {
                        'message': access['service'],
                        'timestamp': timestamp.timestamp() * 1000000,
                        'datetime': timestamp.isoformat(),
                        'timestamp_desc': 'Accessibility TC Last Modified',
                        'extra_field_1': f"client: {access['client']}"
                    }
                    yield ts_event
        except Exception as e:
            print(f"ERROR while extracting timestamp from accessibility_tcc. Reason {str(e)}")

    def a__extract_ts_shutdownlogs(self) -> Generator[dict, None, None]:
        try:
            p = ShutdownLogsParser(self.config, self.case_id)
            data = p.get_result()
            for ts, processes in data.items():
                try:
                    # create timeline entries
                    timestamp = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S%z')
                    for p in processes:
                        ts_event = {
                            'message': p['path'],
                            'timestamp': timestamp.timestamp() * 1000000,
                            'datetime': timestamp.isoformat(),
                            'timestamp_desc': 'Entry in shutdown.log',
                            'extra_field_1': f"pid: {p['pid']}"
                        }
                        yield ts_event
                except Exception as e:
                    print(f"WARNING: shutdownlog entry not parsed: {ts}. Reason: {str(e)}")
        except Exception as e:
            print(f"ERROR while extracting timestamp from shutdownlog. Reason: {str(e)}")

    def a__extract_ts_logarchive(self) -> Generator[dict, None, None]:
        try:
            p = LogarchiveParser(self.config, self.case_id)
            data = p.get_result()
            for trace in data:
                try:
                    # create timeline entry
                    timestamp = LogarchiveParser.convert_unifiedlog_time_to_datetime(trace['time'])
                    ts_event = {
                        'message': trace['message'],
                        'timestamp': timestamp.timestamp() * 1000000,
                        'datetime': trace['datetime'],
                        'timestamp_desc': f"Entry in logarchive: {trace['event_type']}",
                        'extra_field_1': f"subsystem: {trace['subsystem']}; process_uuid: {trace['process_uuid']}; process: {trace['process']}; library: {trace['library']}; library_uuid: {trace['library_uuid']}"
                    }
                    yield ts_event
                except KeyError as e:
                    print(f"WARNING: trace not parsed: {trace}. Error {e}")
        except Exception as e:
            print(f"ERROR while extracting timestamp from logarchive. Reason: {str(e)}")

    def a__extract_ts_wifisecurity(self) -> Generator[dict, None, None]:
        try:
            p = WifiSecurityParser(self.config, self.case_id)
            data = p.get_result()
            for wifi in data:
                # create timeline entry
                ctimestamp = datetime.strptime(wifi['cdat'], '%Y-%m-%d %H:%M:%S %z')
                mtimestamp = datetime.strptime(wifi['mdat'], '%Y-%m-%d %H:%M:%S %z')

                # Event 1: creation
                ts_event = {
                    'message': wifi['acct'],
                    'timestamp': ctimestamp.timestamp() * 1000000,
                    'datetime': ctimestamp.isoformat(),
                    'timestamp_desc': 'SSID added to known secured WIFI list',
                    'extra_field_1': wifi['accc']
                }
                yield ts_event

                # Event 2: modification
                ts_event = {
                    'message': wifi['acct'],
                    'timestamp': mtimestamp.timestamp() * 1000000,
                    'datetime': mtimestamp.isoformat(),
                    'timestamp_desc': 'SSID modified into the secured WIFI list',
                    'extra_field_1': wifi['accc']
                }
                yield ts_event
        except Exception as e:
            print(f"ERROR while extracting timestamp from wifisecurity. Reason {str(e)}")

    def a__extract_ts_wifi_known_networks(self) -> Generator[dict, None, None]:
        try:
            p = WifiKnownNetworksParser(self.config, self.case_id)
            data = p.get_result()
            for item in data.values():
                ssid = item['SSID']
                # WIFI added
                try:
                    added = datetime.strptime(item['AddedAt'], '%Y-%m-%d %H:%M:%S.%f')
                    added = added.replace(tzinfo=timezone.utc)
                    ts_event = {
                        'message': f"WIFI {ssid} added",
                        'timestamp': added.timestamp() * 1000000,
                        'datetime': added.isoformat(),
                        'timestamp_desc': 'added in known networks plist',
                        'extra_field_1': f"Add reason: {item['AddReason']}"
                    }
                    yield ts_event
                except KeyError:
                    # some wifi networks do not have an AddedAt field
                    # print(f"ERROR {filename} while extracting timestamp from {ssid}. Reason: {str(e)}. Record not inserted.")
                    pass

                # WIFI modified
                try:
                    updated = datetime.strptime(item['UpdatedAt'], '%Y-%m-%d %H:%M:%S.%f')
                    updated = updated.replace(tzinfo=timezone.utc)
                    ts_event = {
                        'message': f"WIFI {ssid} updated",
                        'timestamp': updated.timestamp() * 1000000,
                        'datetime': updated.isoformat(),
                        'timestamp_desc': 'updated in known networks plist',
                        'extra_field_1': f"Add reason: {item['AddReason']}"
                    }
                    yield ts_event
                except KeyError:
                    # some wifi networks do not have an UpdatedAt field
                    # print(f"ERROR {filename} while extracting timestamp from {ssid}. Reason: {str(e)}. Record not inserted.")
                    pass

                # Password for wifi modified
                try:
                    modified_password = datetime.strptime(item['__OSSpecific__']['WiFiNetworkPasswordModificationDate'], '%Y-%m-%d %H:%M:%S.%f')
                    modified_password = modified_password.replace(tzinfo=timezone.utc)
                    ts_event = {
                        'message': f"Password for WIFI {ssid} modified",
                        'timestamp': modified_password.timestamp() * 1000000,
                        'datetime': modified_password.isoformat(),
                        'timestamp_desc': 'password modified in known networks plist',
                        'extra_field_1': f"AP mode: {item['__OSSpecific__']['AP_MODE']}"
                    }
                    yield ts_event
                except KeyError:
                    # some wifi networks do not have a password modification date
                    # print(f"ERROR {filename} while extracting timestamp from {ssid}. Reason: {str(e)}. Record not inserted.")
                    pass
        except Exception as e:
            print(f"ERROR while extracting timestamp from wifi_known_networks. Reason {str(e)}")

    def __extract_ts_crashlogs(self) -> Generator[dict, None, None]:
        try:
            p = CrashLogsParser(self.config, self.case_id)
            data = p.get_result()
            # process summary
            for event in data.get('summary', []):
                if event['datetime'] == '':
                    continue
                timestamp = datetime.fromisoformat(event['datetime'])
                ts_event = {
                    'message': f"Application {event['app']} crashed.",
                    'timestamp': timestamp.timestamp() * 1000000,
                    'datetime': event['datetime'],
                    'timestamp_desc': 'Application crash'
                }
                yield ts_event
            # no need to also process the detailed crashes, as we already have the summary
        except Exception as e:
            print(f"ERROR while extracting timestamp from crashlog. Reason {str(e)}")

    def execute(self):
        # Get all the functions that start with '__extract_ts_'
        # and call these with the case_folder as parameter
        # do this using generators, as this eats much less memory and is just so much more efficient
        for func in dir(self):
            if func.startswith(f"_{self.__class__.__name__}__extract_ts_"):
                for event in getattr(self, func)():  # call the function
                    yield event

    def __powerlogs__PLProcessMonitorAgent_EventPoint_ProcessExit(jdata):
        proc_exit = jdata.get('PLProcessMonitorAgent_EventPoint_ProcessExit', [])
        for proc in proc_exit:
            timestamp = datetime.fromtimestamp(proc['timestamp'], tz=timezone.utc)

            extra_field = ''
            if 'IsPermanent' in proc.keys():
                extra_field = f"Is permanent: {proc['IsPermanent']}"
            ts_event = {
                'message': proc['ProcessName'],
                'timestamp': proc['timestamp'] * 1000000,
                'datetime': timestamp.isoformat(),
                'timestamp_desc': f"Process Exit with reason code: {proc['ReasonCode']} reason namespace {proc['ReasonNamespace']}",
                'extra_field_1': extra_field
            }
            yield ts_event

    def __powerlogs__PLProcessMonitorAgent_EventBackward_ProcessExitHistogram(jdata):
        events = jdata.get('PLProcessMonitorAgent_EventBackward_ProcessExitHistogram', [])
        for event in events:
            timestamp = datetime.fromtimestamp(event['timestamp'], tz=timezone.utc)
            ts_event = {
                'message': event['ProcessName'],
                'timestamp': event['timestamp'] * 1000000,
                'datetime': timestamp.isoformat(),
                'timestamp_desc': f"Process Exit with reason code: {event['ReasonCode']} reason namespace {event['ReasonNamespace']}",
                'extra_field_1': f"Crash frequency: [0-5s]: {event['0s-5s']}, [5-10s]: {event['5s-10s']}, [10-60s]: {event['10s-60s']}, [60s+]: {event['60s+']}"
            }
            yield ts_event

    def __powerlogs__PLAccountingOperator_EventNone_Nodes(jdata):
        eventnone = jdata.get('PLAccountingOperator_EventNone_Nodes', [])
        for event in eventnone:
            timestamp = datetime.fromtimestamp(event['timestamp'], tz=timezone.utc)
            ts_event = {
                'message': event['Name'],
                'timestamp': event['timestamp'] * 1000000,
                'datetime': timestamp.isoformat(),
                'timestamp_desc': 'PLAccountingOperator Event',
                'extra_field_1': f"Is permanent: {event['IsPermanent']}"
            }
            yield ts_event
