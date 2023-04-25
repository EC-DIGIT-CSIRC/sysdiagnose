#! /usr/bin/env python3

# For Python3
# Script to parse the brctl-container-list.txt and brctl-dump.txt files
# Author: Emilien Le Jamtel

"""sysdiagnose intialize.

Usage:
  sysdiagnose-brctl.py -i <logfolder>
  sysdiagnose-brctl.py (-h | --help)
  sysdiagnose-brctl.py --version

Options:
  -h --help     Show this screen.
  -v --version     Show version.
"""

import sys
from optparse import OptionParser
import plistlib
import json
from docopt import docopt
from tabulate import tabulate
import glob
import re
import csv
import io


# ----- definition for parsing.py script -----#
# -----         DO NOT DELETE             ----#

parser_description = "Parsing brctl files"
parser_input = "brctl"      # folder containing brctl files
parser_call = "parsebrctl"


def parselistfile(container_list_file):
    containers = {"containers": []}
    result = []
    # print(container_list_file)
    with open(container_list_file[0], 'r') as f:
        keys = ['id', 'localizedName', 'documents', 'Public', 'clients']
        for line in f:
            line = line.strip()
            line = line.replace('Mobile Documents', 'Mobile_Documents')
            keys = ['id', 'localizedName', 'documents', 'Public', 'Private', 'clients']
            values = re.findall(rf"({'|'.join(keys)}):\s*([^ \[]+|\[[^\]]*\])", line)
            result = {k: v.strip('[]') for k, v in values}
            if result != {}:
                result['documents'] = result['documents'].replace('Mobile_Documents', 'Mobile Documents')
                containers['containers'].append(result)
        return containers


def parsedumpfile(container_dump_file):
    with open(container_dump_file[0], 'r') as f:
        dump = {}
        section = "header"
        previous_line = ""
        current_section = ""
        for line in f:
            if line.strip() == "-----------------------------------------------------":
                dump[section] = current_section
                section = previous_line.strip()
                current_section = ""
            else:
                previous_line = line
                current_section += line
        if current_section != "":
            dump[section] = current_section
    # print(dump.keys())

    # parsing different sections
    # header
    header = parse_header(dump['header'])

    # boot_history
    # finding key value
    # loop through the keys of the dictionary
    for key in dump.keys():
        # check if the key starts with "boot_history"
        if key.startswith("boot_history"):
            # print the key and its value
            bhkey = key
    # runing the parser
    boot_history = parse_boot_history(dump[bhkey])

    # server_state
    server_state = parse_server_state(dump['server_state'])

    # client_state
    client_state = parse_client_state(dump['client_state'])

    # system

    system = parse_system_scheduler(dump['system'])

    # scheduler

    system = parse_system_scheduler(dump['scheduler'])

    # containers
    # finding key value
    # loop through the keys of the dictionary
    for key, value in dump.items():
        # check if the key contains "containers matching"
        if "+ app library:" in value:
            # print the key and its value
            ckey = key
    # creating several parser with the same data
    # applibrary
    applibrary = parse_app_library(dump[ckey])

    # server_items
    server_items = parse_server_items(dump[ckey])

    # app library IDs by App ID
    app_library_id, app_ids = parse_apps_monitor(dump['apps monitor'])

    # putting together all the parsed data

    result = {
        "header": header,
        "boot_history": boot_history,
        "server_state": server_state,
        "client_state": client_state,
        "system": system,
        "applibrary": applibrary,
        "server_items": server_items,
        "app_library_id": app_library_id,
        "app_ids": app_ids
    }

    return result


def parse_header(header):
    # Define a regular expression to match the key-value pairs
    pattern = r"(\w+):\s+(.+)(?:\n|$)"

    # Find all the matches in the content
    matches = re.findall(pattern, header)

    # Create an empty dictionary to store the output
    output = {}

    # Loop through the matches and add them to the output dictionary
    for key, value in matches:
        # If the value contains a comma, split it into a list
        if "," in value:
            value = value.split(", ")
        # If the value contains brackets, remove them
        if value.startswith("<") and value.endswith(">"):
            value = value[1:-1]
        # Add the key-value pair to the output dictionary
        output[key] = value

    pattern = r"dump taken at (\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2}) \[account=(\d+)\] \[inCarry=(\w+)\] \[home=(.+)\]"

    # Find the match in the content
    match = re.search(pattern, header)

    # Check if there is a match
    if match:
        # save the values
        output['timestamp'] = match.group(1)
        output['account'] = match.group(2)
        output['inCarry'] = match.group(3)
        output['home'] = match.group(4)

    # Convert the output dictionary to a JSON string
    output_json = json.dumps(output)

    # Print the output JSON string
    return output_json


def parse_boot_history(boot_history):
    # split the section by newline characters
    lines = boot_history.split("\n")
    # initialize an empty list to store the parsed lines
    result = []
    # loop through each line
    for line in lines:
        # parse the line and append it to the result list if not None
        parsed_line = parse_line_boot_history(line)
        if parsed_line:
            result.append(parsed_line)
    # return the result list
    return result


def parse_line_boot_history(line):
    # use regular expressions to extract the fields
    match = re.search(r"\[(.+?)\] OS:(.+?) CloudDocs:(.+?) BirdSchema:(.+?) DBSchema:(.+)", line)
    if match:
        # return a dictionary with the field names and values
        return {
            "date": match.group(1),
            "OS": match.group(2),
            "CloudDocs": match.group(3),
            "BirdSchema": match.group(4),
            "DBSchema": match.group(5)
        }
    else:
        # return None if the line does not match the pattern
        return None


def parse_server_state(server_state):
    # Define the regex pattern to match the fields and their values
    pattern = r"(last-sync|nextRank|minUsedTime):(.+?)(?=\s|$)"

    # Use re.findall to get all the matches as a list of tuples
    matches = re.findall(pattern, server_state)

    # Initialize an empty dictionary to store the parsed data
    output_dict = {}

    # Loop through the matches
    for match in matches:
        # Get the field name and value from the tuple
        field, value = match
        # Replace any dashes with underscores in the field name
        field = field.replace("-", "_")
        # If the field is shared_db, create a nested dictionary for its value
        if field == "shared_db":
            value = {}
        # Add the field-value pair to the output dictionary
        output_dict[field] = value

    # Print the output dictionary
    return output_dict


def parse_client_state(data: str) -> dict:
    # Split the data into lines
    lines = data.split('\n')

    # Initialize an empty dictionary to store the parsed data
    parsed_data = {}

    # Iterate over each line in the data
    for line in lines:
        # Use regular expressions to match key-value pairs
        match = re.match(r'\s*(\w+)\s*=\s*(.*);', line)
        if match:
            key, value = match.groups()
            # Remove any quotes from the value
            value = value.strip('"')
            # Try to convert the value to an integer or float
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
            # Add the key-value pair to the dictionary
            parsed_data[key] = value

    return parsed_data


def parse_system_scheduler(input):
    data = {}
    lines = input.split('\n')
    for line in lines:
        # removing ANSI escape codes
        line = re.sub(r'\x1b\[[0-9;]*m', '', line)
        line = line.strip()
        if line.startswith('+'):
            key, value = line.split(':', 1)
            key = key.strip().replace('+', '').strip()
            value = value.strip()
            data[key] = value
    return data


def parse_app_library(data):
    lines = data.splitlines()
    matching_lines = [line for line in lines if "+ app library" in line]

    pattern = r'<(.*?)\[(\d+)\].*?ino:(\d+).*?apps:\{(.*?)\}.*?bundles:\{(.*?)\}'
    matches = re.findall(pattern, '\n'.join(matching_lines))

    result = []
    for match in matches:
        library = match[0]
        app_id = match[1]
        ino = match[2]
        apps = match[3].split('; ')
        bundles = match[4].split(', ')
        result.append({'library': library, 'ino': ino, 'apps': apps, 'bundles': bundles})

    return result


def parse_server_items(data):
    lines = data.splitlines()
    matching_lines = [line for line in lines if "----------------------" in line]

    app_list = []

    for line in matching_lines:
        pattern = r'-+([^\[]+)\[(\d+)\]-+'
        match = re.search(pattern, line)

        if match:
            library_name = match.group(1)
            library_id = match.group(2)
            app_list.append({'library_name': library_name, 'library_id': library_id})

    return app_list


def parse_apps_monitor(data):
    # Split the text into two parts
    parts = data.split("=======================")

    # Extract the JSON strings from each part
    json_str1 = parts[1].strip().replace("=", ":").replace("\\", "").replace(
        "\"{(n    \"", "[\"").replace("\"n)}\"", "\"]").replace(",n    ", ",").replace(";", ",")
    json_str2 = parts[2].strip().replace("=", ":").replace("\\", "").replace(
        "\"{(n    \"", "[\"").replace("\"n)}\"", "\"]").replace(",n    ", ",").replace(";", ",")

    # ugly fixes
    last_comma_index = json_str1.rfind(",")
    json_str1_new = json_str1[:last_comma_index] + json_str1[last_comma_index + 1:]

    first_brace_index = json_str1_new.find("}")
    json_str1 = json_str1_new[:first_brace_index + 1]

    # ugly fixes
    last_comma_index = json_str2.rfind(",")
    json_str2_new = json_str2[:last_comma_index] + json_str2[last_comma_index + 1:]

    first_brace_index = json_str2_new.find("}")
    json_str2 = json_str2_new[:first_brace_index + 1]

    # Load the JSON strings into Python dictionaries
    json1 = json.loads(json_str1)
    json2 = json.loads(json_str2)

    return json1, json2


def parsebrctl(brctl_folder):
    container_list_file = [brctl_folder + '/brctl-container-list.txt']
    container_dump_file = [brctl_folder + '/brctl-dump.txt']

    brctl_parsing = {**parselistfile(container_list_file), **parsedumpfile(container_dump_file)}

    return brctl_parsing


def main():
    """
        Main function, to be called when used as CLI tool
    """

    if sys.version_info[0] < 3:
        print("Must be using Python 3! Exiting ...")
        exit(-1)

    arguments = docopt(__doc__, version='parser for brctl files v0.1')

    if arguments['-i']:
        try:
            container_list_file = glob.glob(arguments['<logfolder>'] + 'brctl-container-list.txt')
            container_dump_file = glob.glob(arguments['<logfolder>'] + 'brctl-dump.txt')

            brctl_parsing = {**parselistfile(container_list_file), **parsedumpfile(container_dump_file)}

            print(json.dumps(brctl_parsing, indent=4))
        except Exception as e:
            print(f'error retrieving log files. Reason: {str(e)}')

    return


"""
   Call main function
"""
if __name__ == "__main__":
    # Create an instance of the Analysis class (called "base") and run main
    main()
