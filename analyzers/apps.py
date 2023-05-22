#! /usr/bin/env python3

# For Python3
# DEMO - Skeleton
# Author: Emiliern Le Jamtel

"""Apps analyzer.

Usage:
  apps.py -i <logfolder>
  apps.py (-h | --help)
  apps.py --version

Options:
  -h --help     Show this screen.
  -v --version     Show version.
"""
import os
from optparse import OptionParser
import json
import ijson
from docopt import docopt
import glob

version_string = "sysdiagnose-demo-analyser.py v2023-04-28 Version 0.1"

# ----- definition for analyse.py script -----#
# -----         DO NOT DELETE             ----#

analyser_description = "Get list of Apps installed on the device"
analyser_call = "apps_analysis"
analyser_format = "md"

# --------------------------------------------------------------------------- #

def apps_analysis(jsondir, filename):
    """
    Go through all json files in the folder and generate the markdown file
    """

    apps = {}

    # building data depending on the source
    for jsonfile in jsondir:
        if jsonfile.endswith('accessibility-tcc.json'):
            with open(jsonfile, 'r') as f:
                accessibility_data = json.load(f)
                for entry in accessibility_data['access']:
                    if entry['client'] not in apps.keys():
                        apps[entry['client']]= {"found": ['accessibility-tcc'], "services": [entry['service']]}
                    else:
                        apps[entry['client']]["services"].append(entry['service'])
        elif jsonfile.endswith('brctl.json'):
            with open(jsonfile, 'r') as f:
                brctl_data = json.load(f)
                # directly going to the list of apps
                for entry in brctl_data['app_library_id'].keys():
                    if entry not in apps.keys():
                        apps[entry]= {"found": ['brctl'], "libraries": brctl_data['app_library_id'][entry]}
                    else:
                        apps[entry]["libraries"] = brctl_data['app_library_id'][entry]
                        apps[entry]["found"].append('brctl')
        elif jsonfile.endswith('itunesstore.json'):
            with open(jsonfile, 'r') as f:
                itunesstore_data = json.load(f)
                # directly going to the list of apps
                for entry in itunesstore_data['application_id']:
                    if entry['bundle_id'] not in apps.keys():
                        apps[entry['bundle_id']]= {"found": ['itunesstore']}
                    else:
                        apps[entry['bundle_id']]["found"].append('itunesstore')
        elif jsonfile.endswith('logarchive.json'):
            # try something simple
            app_list = []
            with open(jsonfile, 'rb') as f:
                for entry in ijson.items(f, 'data.item'):
                    if entry['subsystem'] not in app_list:
                        app_list.append(entry['subsystem'])
                        print(entry['subsystem'])
    # print(json.dumps(apps, indent=4))

    return


# --------------------------------------------------------------------------- #
"""
    Main function
"""
def main():
    """
        Main function, to be called when used as CLI tool
    """

    arguments = docopt(__doc__, version='parser for com.apple.wifi plist files v0.2')

    if arguments['-i']:
        # go through the json files in the folder
        json_files = []
        for file in os.listdir(arguments['<logfolder>']):
            if file.endswith(".json"):
                json_files.append(os.path.join(arguments['<logfolder>'], file))
        # call the function to generate the apps analysis
        apps_analysis(json_files, 'tmp.md')

# --------------------------------------------------------------------------- #


"""
   Call main function
"""

if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folks ;)
