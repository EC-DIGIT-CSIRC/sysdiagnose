#! /usr/bin/env python3

# For Python3
# Script to parse the brctl-container-list.txt and brctl-dump.txt files
# Author: Emilien Le Jamtel
import json
import re
import os
from sysdiagnose.utils.base import BaseParserInterface

# TODO brctl analyser for boot_history section -> timeline


class BrctlParser(BaseParserInterface):
    description = "Parsing brctl files"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_folders = [
            'brctl/'
        ]
        return [os.path.join(self.case_data_subfolder, log_folder) for log_folder in log_folders]

    def execute(self) -> list | dict:
        try:
            return BrctlParser.parse_folder(self.get_log_files()[0])
        except IndexError:
            return {'error': 'No brctl folder found'}

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
        header = BrctlParser.parse_header(dump['header'])

        # boot_history
        # finding key value
        # loop through the keys of the dictionary
        for key in dump.keys():
            # check if the key starts with "boot_history"
            if key.startswith("boot_history"):
                # print the key and its value
                bhkey = key
        # runing the parser
        try:
            boot_history = BrctlParser.parse_boot_history(dump[bhkey])
        except UnboundLocalError:
            boot_history = {}

        # server_state
        try:
            server_state = BrctlParser.parse_server_state(dump['server_state'])
        except KeyError:
            server_state = {}

        # client_state
        try:
            client_state = BrctlParser.parse_client_state(dump['client_state'])
        except KeyError:
            client_state = {}

        # system
        try:
            system = BrctlParser.parse_system_scheduler(dump['system'])
        except KeyError:
            system = {}

        # scheduler
        try:
            scheduler = BrctlParser.parse_system_scheduler(dump['scheduler'])
        except KeyError:
            scheduler = {}

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
        try:
            applibrary = BrctlParser.parse_app_library(dump[ckey])
        except UnboundLocalError:
            applibrary = {}

        # server_items
        try:
            server_items = BrctlParser.parse_server_items(dump[ckey])
        except UnboundLocalError:
            server_items = {}

        # app library IDs by App ID
        try:
            app_library_id, app_ids = BrctlParser.parse_apps_monitor(dump['apps monitor'])
        except KeyError:
            app_library_id = {}
            app_ids = {}
        # putting together all the parsed data

        result = {
            "header": header,
            "boot_history": boot_history,
            "server_state": server_state,
            "client_state": client_state,
            "system": system,
            "scheduler": scheduler,
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
            parsed_line = BrctlParser.parse_line_boot_history(line)
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
            app_id = match[1]  # noqa F841
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
        json_str1 = BrctlParser.__parse_apps_monitor2json(parts[1].strip())
        json_str2 = BrctlParser.__parse_apps_monitor2json(parts[2].strip())

        # Load the JSON strings into Python dictionaries
        json1 = json.loads(json_str1)
        json2 = json.loads(json_str2)

        return json1, json2

    def __parse_apps_monitor2json(data):
        # replace = by :
        json_str = data.replace("=", ":")
        # remove literal string '\n'
        json_str = re.sub(r'\\n\s*', '', json_str)
        # remove char \
        # replace start of array string representation "{( by [
        # replace end of array string representation )}" by ]
        # remove char "
        json_str = json_str.replace("\\", "").replace('"{(', '[').replace(')}";', '],').replace('"', '')
        # adds double quotes to all bundle IDs or library IDs
        json_str = re.sub(r'([\w\.\-]+)', r'"\1"', json_str)

        # ugly fixes
        last_comma_index = json_str.rfind(",")
        json_str_new = json_str[:last_comma_index] + json_str[last_comma_index + 1:]

        first_brace_index = json_str_new.find("}")
        json_str = json_str_new[:first_brace_index + 1]

        return json_str

    def parse_folder(brctl_folder):
        container_list_file = [os.path.join(brctl_folder, 'brctl-container-list.txt')]
        container_dump_file = [os.path.join(brctl_folder, 'brctl-dump.txt')]
        if os.path.exists(container_list_file[0]) and os.path.exists(container_dump_file[0]):
            brctl_parsing = {**BrctlParser.parselistfile(container_list_file), **BrctlParser.parsedumpfile(container_dump_file)}
            return brctl_parsing
        return {}
