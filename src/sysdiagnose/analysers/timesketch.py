#! /usr/bin/env python3

# For Python3
# Script to extract timestamp and generate a timesketch output
# Author: david@autopsit.org
#

from datetime import datetime, timezone
from sysdiagnose.parsers.logarchive import LogarchiveParser
from sysdiagnose.parsers.mobileactivation import MobileActivationParser
from sysdiagnose.parsers.powerlogs import PowerLogsParser
from sysdiagnose.parsers.swcutil import SwcutilParser
from sysdiagnose.parsers.accessibility_tcc import AccessibilityTccParser
from sysdiagnose.parsers.shutdownlogs import ShutdownLogsParser
from sysdiagnose.parsers.wifisecurity import WifiSecurityParser
from sysdiagnose.parsers.wifi_known_networks import WifiKnownNetworksParser
from sysdiagnose.parsers.crashlogs import CrashLogsParser
from collections.abc import Generator
from sysdiagnose.utils.base import BaseAnalyserInterface, logger


class TimesketchAnalyser(BaseAnalyserInterface):
    description = 'Generate a Timesketch compatible timeline'
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    # Timesketch format:
    # https://timesketch.org/guides/user/import-from-json-csv/
    # Mandatory: timestamps must be in microseconds !!!
    # {"message": "A message","timestamp": 123456789,"datetime": "2015-07-24T19:01:01+00:00","timestamp_desc": "Write time","extra_field_1": "foo"}

    def __extract_ts_mobileactivation(self) -> Generator[dict, None, None]:
        try:
            p = MobileActivationParser(self.config, self.case_id)
            data = p.get_result()
            for event in data:
                ts_event = {
                    'message': event['msg'],
                    'timestamp': event['timestamp'] * 1000000,
                    'datetime': event['datetime'],
                    'timestamp_desc': 'Mobile Activation Time'
                }
                try:
                    ts_event['extra_field_1'] = f"Build Version: {event['build_version']}"
                except KeyError:
                    # skip other type of event
                    # FIXME what should we do? the log file (now) contains nice timestamps, do we want to extract less, but summarized, data?
                    pass
                yield ts_event
        except Exception as e:
            logger.exception("ERROR while extracting timestamp from mobileactivation file.")

    def __extract_ts_powerlogs(self) -> Generator[dict, None, None]:
        try:
            p = PowerLogsParser(self.config, self.case_id)
            data = p.get_result()
            for event in data:
                if event.get('db_table') == 'PLProcessMonitorAgent_EventPoint_ProcessExit':
                    extra_field = ''
                    if 'IsPermanent' in event:
                        extra_field = f"Is permanent: {event['IsPermanent']}"
                    ts_event = {
                        'message': event['ProcessName'],
                        'timestamp': event['timestamp'] * 1000000,
                        'datetime': event['datetime'],
                        'timestamp_desc': f"Process Exit with reason code: {event['ReasonCode']} reason namespace {event['ReasonNamespace']}",
                        'extra_field_1': extra_field
                    }
                    yield ts_event
                elif event.get('db_table') == 'PLProcessMonitorAgent_EventBackward_ProcessExitHistogram':
                    ts_event = {
                        'message': event['ProcessName'],
                        'timestamp': event['timestamp'] * 1000000,
                        'datetime': event['datetime'],
                        'timestamp_desc': f"Process Exit with reason code: {event['ReasonCode']} reason namespace {event['ReasonNamespace']}",
                        'extra_field_1': f"Crash frequency: [0-5s]: {event['0s-5s']}, [5-10s]: {event['5s-10s']}, [10-60s]: {event['10s-60s']}, [60s+]: {event['60s+']}"
                    }
                    yield ts_event
                elif event.get('db_table') == 'PLAccountingOperator_EventNone_Nodes':
                    ts_event = {
                        'message': event['Name'],
                        'timestamp': event['timestamp'] * 1000000,
                        'datetime': event['datetime'],
                        'timestamp_desc': 'PLAccountingOperator Event',
                        'extra_field_1': f"Is permanent: {event['IsPermanent']}"
                    }
                    yield ts_event
                else:
                    pass

        except Exception as e:
            logger.exception("ERROR while extracting timestamp from powerlogs.")

    def __extract_ts_swcutil(self) -> Generator[dict, None, None]:
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
                            'datetime': timestamp.isoformat(timespec='microseconds'),
                            'timestamp_desc': 'swcutil last checked',
                            'extra_field_1': f"application: {service['App ID']}"
                        }
                        yield ts_event
                    except KeyError:
                        # some entries do not have a Last Checked or timestamp field
                        logger.warning(f"Error while extracting timestamp from {(service['Service'])} - {(service['App ID'])}. Record not inserted.")
                        pass
        except Exception as e:
            logger.exception("ERROR while extracting timestamp from swcutil.")

    def __extract_ts_accessibility_tcc(self) -> Generator[dict, None, None]:
        try:
            p = AccessibilityTccParser(self.config, self.case_id)
            data = p.get_result()

            for item in data:
                if item['db_table'] != 'access':
                    continue
                # create timeline entry
                timestamp = datetime.fromtimestamp(item['last_modified'], tz=timezone.utc)
                ts_event = {
                    'message': item['service'],
                    'timestamp': timestamp.timestamp() * 1000000,
                    'datetime': timestamp.isoformat(timespec='microseconds'),
                    'timestamp_desc': 'Accessibility TC Last Modified',
                    'extra_field_1': f"client: {item['client']}"
                }
                yield ts_event
        except Exception as e:
            logger.exception("ERROR while extracting timestamp from accessibility_tcc.")

    def __extract_ts_shutdownlogs(self) -> Generator[dict, None, None]:
        try:
            p = ShutdownLogsParser(self.config, self.case_id)
            data = p.get_result()
            for event in data:
                try:
                    # create timeline entries
                    ts_event = {
                        'message': event['path'],
                        'timestamp': event['timestamp'] * 1000000,
                        'datetime': event['datetime'],
                        'timestamp_desc': 'Entry in shutdown.log',
                        'extra_field_1': f"pid: {event['pid']}"
                    }
                    yield ts_event
                except Exception as e:
                    logger.warning(f"WARNING: shutdownlog entry not parsed: {event}", exc_info=True)
        except Exception as e:
            logger.exception("ERROR while extracting timestamp from shutdownlog.")

    def __extract_ts_logarchive(self) -> Generator[dict, None, None]:
        try:
            p = LogarchiveParser(self.config, self.case_id)
            data = p.get_result()
            for event in data:
                try:
                    # create timeline entry
                    ts_event = {
                        'message': event['message'],
                        'timestamp': event['timestamp'] * 1000000,
                        'datetime': event['datetime'],
                        'timestamp_desc': f"Entry in logarchive: {event['event_type']}",
                        'extra_field_1': f"subsystem: {event['subsystem']}; process_uuid: {event['process_uuid']}; process: {event['process']}; library: {event['library']}; library_uuid: {event['library_uuid']}"
                    }
                    yield ts_event
                except KeyError as e:
                    logger.warning(f"WARNING: trace not parsed: {event}.", exc_info=True)
        except Exception as e:
            logger.exception(f"ERROR while extracting timestamp from logarchive.")

    def __extract_ts_wifisecurity(self) -> Generator[dict, None, None]:
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
                    'datetime': ctimestamp.isoformat(timespec='microseconds'),
                    'timestamp_desc': 'SSID added to known secured WIFI list',
                    'extra_field_1': wifi['accc']
                }
                yield ts_event

                # Event 2: modification
                ts_event = {
                    'message': wifi['acct'],
                    'timestamp': mtimestamp.timestamp() * 1000000,
                    'datetime': mtimestamp.isoformat(timespec='microseconds'),
                    'timestamp_desc': 'SSID modified into the secured WIFI list',
                    'extra_field_1': wifi['accc']
                }
                yield ts_event
        except Exception as e:
            logger.exception("ERROR while extracting timestamp from wifisecurity.")

    def __extract_ts_wifi_known_networks(self) -> Generator[dict, None, None]:
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
                        'datetime': added.isoformat(timespec='microseconds'),
                        'timestamp_desc': 'added in known networks plist',
                        'extra_field_1': f"Add reason: {item['AddReason']}"
                    }
                    yield ts_event
                except KeyError:
                    # some wifi networks do not have an AddedAt field
                    logger.warning(f"Error while extracting timestamp from {ssid}. Record not inserted.", exc_info=True)
                    pass

                # WIFI modified
                try:
                    updated = datetime.strptime(item['UpdatedAt'], '%Y-%m-%d %H:%M:%S.%f')
                    updated = updated.replace(tzinfo=timezone.utc)
                    ts_event = {
                        'message': f"WIFI {ssid} updated",
                        'timestamp': updated.timestamp() * 1000000,
                        'datetime': updated.isoformat(timespec='microseconds'),
                        'timestamp_desc': 'updated in known networks plist',
                        'extra_field_1': f"Add reason: {item['AddReason']}"
                    }
                    yield ts_event
                except KeyError:
                    # some wifi networks do not have an UpdatedAt field
                    logger.warning(f"Error while extracting timestamp from {ssid}.Record not inserted.", exc_info=True)
                    pass

                # Password for wifi modified
                try:
                    modified_password = datetime.strptime(item['__OSSpecific__']['WiFiNetworkPasswordModificationDate'], '%Y-%m-%d %H:%M:%S.%f')
                    modified_password = modified_password.replace(tzinfo=timezone.utc)
                    ts_event = {
                        'message': f"Password for WIFI {ssid} modified",
                        'timestamp': modified_password.timestamp() * 1000000,
                        'datetime': modified_password.isoformat(timespec='microseconds'),
                        'timestamp_desc': 'password modified in known networks plist',
                        'extra_field_1': f"AP mode: {item['__OSSpecific__']['AP_MODE']}"
                    }
                    yield ts_event
                except KeyError:
                    # some wifi networks do not have a password modification date
                    logger.warning(f"Error while extracting timestamp from {ssid}. Record not inserted.", exc_info=True)
                    pass
        except Exception as e:
            logger.exception("ERROR while extracting timestamp from wifi_known_networks.")

    def __extract_ts_crashlogs(self) -> Generator[dict, None, None]:
        try:
            p = CrashLogsParser(self.config, self.case_id)
            data = p.get_result()
            # process summary
            for event in data:
                try:
                    if event['datetime'] == '':
                        continue
                    ts_event = {
                        'message': f"Application {event['app_name']} crashed.",
                        'timestamp': event['timestamp'] * 1000000,
                        'datetime': event['datetime'],
                        'timestamp_desc': 'Application crash'
                    }
                    yield ts_event
                # no need to also process the detailed crashes, as we already have the summary
                except KeyError:
                    # skip bug_type fields
                    pass
        except Exception as e:
            logger.exception("ERROR while extracting timestamp from crashlog.")

    def execute(self):
        # Get all the functions that start with '__extract_ts_'
        # and call these with the case_folder as parameter
        # do this using generators, as this eats much less memory and is just so much more efficient
        for func in dir(self):
            if func.startswith(f"_{self.__class__.__name__}__extract_ts_"):
                for event in getattr(self, func)():  # call the function
                    yield event
