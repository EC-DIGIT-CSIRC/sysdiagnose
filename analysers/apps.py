#! /usr/bin/env python3

# For Python3
# Author: Emiliern Le Jamtel

import re
from utils.base import BaseAnalyserInterface
from parsers.accessibility_tcc import AccessibilityTccParser
from parsers.brctl import BrctlParser
from parsers.itunesstore import iTunesStoreParser
from parsers.logarchive import LogarchiveParser


class AppsAnalyser(BaseAnalyserInterface):
    description = 'Get list of Apps installed on the device'
    format = 'json'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    # this code is quite slow, but that's due to logarchive.jsonl being slow to parse
    def execute(self):
        '''
        Go through all json files in the folder and generate the json list of apps
        '''
        apps = {}
        json_data = AccessibilityTccParser(self.config, self.case_id).get_result()
        for entry in json_data:
            if entry['db_table'] != 'access':
                continue
            try:
                try:
                    apps[entry['client']]['services'].append(entry['service'])
                except KeyError:
                    apps[entry['client']]['services'] = [entry['service']]
            except (KeyError, TypeError):
                apps[entry['client']] = {'found': ['accessibility-tcc'], 'services': [entry['service']]}

        json_data = BrctlParser(self.config, self.case_id).get_result()
        if json_data and not json_data.get('error'):
            # directly going to the list of apps
            for entry in json_data['app_library_id']:
                try:
                    try:
                        apps[entry]['libraries'] = json_data['app_library_id'][entry]
                    except KeyError:
                        apps[entry['client']]['libraries'] = json_data['app_library_id'][entry]

                    apps[entry]['found'].append('brctl')

                except (KeyError, TypeError):
                    apps[entry] = {'found': ['brctl'], 'libraries': json_data['app_library_id'][entry]}

        json_data = iTunesStoreParser(self.config, self.case_id).get_result()
        if json_data and not json_data.get('error'):
            # directly going to the list of apps
            for entry in json_data['application_id']:
                try:
                    apps[entry['bundle_id']]['found'].append('itunesstore')
                except (KeyError, TypeError):
                    apps[entry['bundle_id']] = {'found': ['itunesstore']}

        re_bundle_id_pattern = r'(([a-zA-Z0-9-_]+\.)+[a-zA-Z0-9-_]+)'
        # list files in here
        json_entries = LogarchiveParser(self.config, self.case_id).get_result()
        for entry in json_entries:
            try:
                # skip empty entries
                if entry['subsystem'] == '':
                    continue
            except KeyError:  # last line of the native logarchive.jsonl file
                continue

            # extract app/bundle id or process name from the subsystem field
            if not re.search(r'^' + re_bundle_id_pattern + r'$', entry['subsystem']):
                # extract foo.bar.hello from the substing if it is in that format
                matches = re.findall(re_bundle_id_pattern, entry['subsystem'])
                if matches:
                    new_term = matches[0][0]
                else:
                    # below are not really apps...more processes.
                    # TODO decide if we want to keep them or not.
                    matches = re.findall(r'\[([a-zA-Z0-9-_]+)\]', entry['subsystem'])
                    if matches:
                        new_term = matches[0]
                    else:
                        matches = re.findall(r'^([a-zA-Z0-9-_]+)$', entry['subsystem'])
                        if matches:
                            new_term = matches[0]
                        else:
                            # print(f"Skipping entry: {entry['subsystem']}")
                            continue
                # print(f"New entry: {new_term} - was: {entry['subsystem']}")
                entry['subsystem'] = new_term
            # add it to the list
            try:
                if 'logarchive' not in apps[entry['subsystem']]['found']:
                    apps[entry['subsystem']]['found'].append('logarchive')

            except (KeyError, TypeError):
                apps[entry['subsystem']] = {'found': ['logarchive']}

        return apps
