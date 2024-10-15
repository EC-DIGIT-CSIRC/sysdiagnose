#! /usr/bin/env python3

# For Python3
# Script to print WIFI info from ./WiFi/security.txt
# Author: david@autopsit.org

import os
from sysdiagnose.utils.base import BaseParserInterface
import logging

logger = logging.getLogger('sysdiagnose')


class WifiSecurityParser(BaseParserInterface):
    description = "Parsing WiFi Security logs"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        """
            Get the list of log files to be parsed
        """
        log_files = [
            "WiFi/security.txt"
        ]
        return [os.path.join(self.case_data_subfolder, log_files) for log_files in log_files]

    def execute(self) -> list | dict:
        return WifiSecurityParser.parse_file(self.get_log_files()[0])

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
                        entries.append(element)
                        logger.debug(f"appending {element}")
                        element = {}
        except IndexError:
            return {'error': 'No WiFi/security.txt file present'}
        except Exception as e:
            logger.error(f"Could not parse: {path}. Reason: {str(e)}")
            return {'error': f'Could not parse: {path}. Reason: {str(e)}'}
        return entries
