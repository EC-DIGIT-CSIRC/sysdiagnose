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

    # TODO this code is terribly slow. I would expect this is due to all the if key in lookups. It took 49 seconds for case 1
    def execute(self):
        '''
        Go through all json files in the folder and generate the json list of apps
        '''
        apps = {}
        # TODO add a check to see if the files exist, and if necessary, call the parsers (or ask the user to call them), or maybe using a flag in the function call

        json_data = AccessibilityTccParser(self.config, self.case_id).get_result()
        if json_data and not json_data.get('error'):
            for entry in json_data['access']:
                if entry['client'] not in apps:
                    apps[entry['client']] = {'found': ['accessibility-tcc'], 'services': [entry['service']]}
                else:
                    try:
                        apps[entry['client']]['services'].append(entry['service'])
                    except KeyError:
                        apps[entry['client']]['services'] = [entry['service']]

        json_data = BrctlParser(self.config, self.case_id).get_result()
        if json_data and not json_data.get('error'):
            # directly going to the list of apps
            for entry in json_data['app_library_id']:
                if entry not in apps:
                    apps[entry] = {'found': ['brctl'], 'libraries': json_data['app_library_id'][entry]}
                else:
                    try:
                        apps[entry]['libraries'] = json_data['app_library_id'][entry]
                    except KeyError:
                        apps[entry['client']]['libraries'] = json_data['app_library_id'][entry]

                    apps[entry]['found'].append('brctl')

        json_data = iTunesStoreParser(self.config, self.case_id).get_result()
        if json_data and not json_data.get('error'):
            # directly going to the list of apps
            for entry in json_data['application_id']:
                if entry['bundle_id'] not in apps:
                    apps[entry['bundle_id']] = {'found': ['itunesstore']}
                else:
                    apps[entry['bundle_id']]['found'].append('itunesstore')

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
            if entry['subsystem'] not in apps:
                apps[entry['subsystem']] = {'found': ['logarchive']}
            else:
                if 'logarchive' not in apps[entry['subsystem']]['found']:
                    apps[entry['subsystem']]['found'].append('logarchive')

        return apps
