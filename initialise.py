#! /usr/bin/env python

# For Python3
# Initializing sysdiagnose Analysis
# Extract archive and create a json file containing information necessary for Analysis
# version, path_to_extracted_files, etc...

"""sysdiagnose initialize.

Usage:
  initialise.py file <sysdiagnose_file> [--force]
  initialise.py (-h | --help)
  initialise.py --version

Options:
  -h --help     Show this screen.
  -v --version     Show version.
"""

import config

import sys
import os
import tarfile
import json
import hashlib
import glob
from docopt import docopt

from utils.misc import get_version

version = get_version()


"""
    Init function
"""


def init(sysdiagnose_file, force=False):
    # open case json file
    try:
        with open(config.cases_file, 'r') as f:
            cases = json.load(f)
    except Exception as e:
        print(f'error opening cases json file - check config.py. Failure reason: f{str(e)}')
        sys.exit()

    # calculate sha256 of sysdiagnose file and compare with past cases
    try:
        with open(sysdiagnose_file, 'rb') as f:
            bytes = f.read()  # read entire file as bytes
            readable_hash = hashlib.sha256(bytes).hexdigest()
            print(readable_hash)
    except Exception as e:
        print(f'error calculating sha256. Reason: {str(e)}')
    case_id = 0
    for case in cases['cases']:
        # Take the opportunity to find the highest case_id
        case_id = max(case_id, case['case_id'])
        if readable_hash == case['source_sha256']:
            if force:
                case_id = case['case_id'] - 1
            else:
                print(f"this sysdiagnose has already been extracted : caseID: {str(case['case_id'])}")
                sys.exit()

    # test sysdiagnose file
    try:
        tf = tarfile.open(sysdiagnose_file)
    except Exception as e:
        print(f'error opening sysdiagnose file. Reason: {str(e)}')
        sys.exit()

    # if sysdiagnose file is new and legit, create new case and extract files
    # create case dictionnary
    new_case = {
        "case_id": case_id + 1,
        "source_file": sysdiagnose_file,
        "source_sha256": readable_hash,
        "case_file": config.data_folder + str(case_id + 1) + ".json"
    }
    # create case folder
    new_folder = config.data_folder + str(new_case['case_id'])
    if not os.path.exists(new_folder):
        os.makedirs(new_folder)

    # create parsed_data folder
    new_parsed_folder = config.parsed_data_folder + str(new_case['case_id'])
    if not os.path.exists(new_parsed_folder):
        os.makedirs(new_parsed_folder)

    # extract sysdiagnose files
    if config.debug:
        print(f"cd'ing to {new_folder}")
    prev_folder = os.getcwd()
    os.chdir(new_folder)
    try:
        tf.extractall()
    except Exception as e:
        print(f'Error while decompressing sysdiagnose file. Reason: {str(e)}')

    # create case json file
    new_case_json = {
        "sysdiagnose.log": new_folder + glob.glob('./*/sysdiagnose.log')[0][1:],
    }

    # ips files
    try:
        ips_files = glob.glob('./*/crashes_and_spins/*.ips')
        ips_files_fullpath = []
        for ips in ips_files:
            ips = new_folder + ips[1:]
            ips_files_fullpath.append(ips)
        new_case_json["ips_files"] = ips_files_fullpath
    except:        # noqa: E722
        pass

    # print(json.dumps(new_case_json, indent=4))

    # Get iOS version
    if config.debug:
        print("cd'ing to ../..")
    os.chdir('../..')
    try:
        with open(new_case_json['sysdiagnose.log'], 'r') as f:
            line_version = [line for line in f if 'iPhone OS' in line][0]
            version = line_version.split()[4]
        new_case_json['ios_version'] = version
    except Exception as e:
        print(f"Could not open file {new_case_json['sysdiagnose.log']}. Reason: {str(e)}")
        sys.exit()

    # Save JSON file
    with open(new_case['case_file'], 'w') as data_file:
        data_file.write(json.dumps(new_case_json, indent=4))

    # update cases list file
    cases['cases'].append(new_case)

    with open(config.cases_file, 'w') as data_file:
        data_file.write(json.dumps(cases, indent=4))

    print("Sysdiagnose file has been processed")
    print(f"New case ID: {str(new_case['case_id'])}")
    os.chdir(prev_folder)


"""
    Integrity Checking (cases files and folders)
"""


def integrity_check():
    if not os.path.exists(config.data_folder):
        os.makedirs(config.data_folder)
    if not os.path.exists(config.parsed_data_folder):
        os.makedirs(config.parsed_data_folder)
    if not os.path.exists(config.cases_file):
        cases = {'cases': []}
        with open(config.cases_file, 'w') as data_file:
            data_file.write(json.dumps(cases, indent=4))


"""
    Main function
"""


def main():

    if sys.version_info[0] < 3:
        print("Still using Python 2 ?!?")
        sys.exit(-1)

    arguments = docopt(__doc__, version=f'Sysdiagnose initialize script {version}')

    integrity_check()

    if arguments['file']:
        if os.path.realpath(arguments['<sysdiagnose_file>']):
            init(arguments['<sysdiagnose_file>'], arguments['--force'])
        else:
            print("file not found")
            sys.exit()


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()
