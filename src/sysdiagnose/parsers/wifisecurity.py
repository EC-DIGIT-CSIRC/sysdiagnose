#! /usr/bin/env python3

# For Python3
# Script to print WIFI info from ./WiFi/security.txt
# Author: david@autopsit.org

import glob
import os
from sysdiagnose.utils.base import BaseParserInterface, SysdiagnoseConfig, logger, Event
from datetime import datetime


class WifiSecurityParser(BaseParserInterface):
    description = "Parsing WiFi Security logs"
    format = "jsonl"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        """
            Get the list of log files to be parsed
        """
        log_files_globs = [
            "WiFi/security.txt"
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        for log_file in self.get_log_files():
            return WifiSecurityParser.parse_file(log_file)
        return {'error': ['No WiFi/security.txt file present']}

    def parse_file(path: str) -> list | dict:
        """
            Parse ./WiFi/security.txt and extract block of interest:

                accc : <SecAccessControlRef: ck>
                acct : <WIFI SSID>
                agrp : apple
                cdat : 2023-02-09 21:10:38 +0000
                desc : <WIFI DESCRIPTION>
                labl : <WIFI LABEL>
                mdat : 2023-02-09 21:10:38 +0000
                musr : {length = 0, bytes = 0x}
                pdmn : ck
                sha1 : {length = 20, bytes = 0x98146b802675fb480dc64a8f3a7597ea70f03b46}
                svce : AirPort
                sync : 1
                tomb : 0
        """
        entries = []
        element = {}
        try:
            with open(path, "r") as f:
                for line in f:
                    if ' : ' in line:
                        key, value = line.split(" : ")
                        logger.debug(f"key: {key.strip()}, value: {value.strip()}")
                        element[key.strip()] = value.strip()
                    elif element:
                        # created
                        timestamp = datetime.strptime(element['cdat'], "%Y-%m-%d %H:%M:%S %z")
                        event = Event(
                            datetime=timestamp,
                            message=f"Wifi AP config: {element.get('desc', '')} # {element.get('labl', '')} # {element.get('acct', '')}",
                            module='wifi_security',
                            timestamp_desc='wifi AP config created',
                            data=element
                        )
                        entries.append(event.to_dict())

                        if element['mdat'] != element['cdat']:
                            # also add the modified date
                            timestamp = datetime.strptime(element['mdat'], "%Y-%m-%d %H:%M:%S %z")
                            event_mdat = Event(
                                datetime=timestamp,
                                message=f"Wifi AP config: {element.get('desc', '')} # {element.get('labl', '')} # {element.get('acct', '')}",
                                module='wifi_security',
                                timestamp_desc='wifi AP config modified',
                                data=element
                            )
                            entries.append(event_mdat.to_dict())

                        # reset element for next entry
                        element = {}
        except IndexError:
            return {'error': 'No WiFi/security.txt file present'}
        except Exception as e:
            logger.exception(f"Could not parse: {path}")
            return {'error': f'Could not parse: {path}. Reason: {str(e)}'}
        return entries
