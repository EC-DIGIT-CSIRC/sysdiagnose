import os

"""
This file contains all of the configuration values for the project.
"""


config_folder = os.path.dirname(os.path.abspath(__file__))
parsers_folder = os.path.join(config_folder, "parsers")
analysers_folder = os.path.join(config_folder, "analysers")

# case data is in current working directory
cases_file = os.path.join('.', "cases.json")
data_folder = os.path.join('.', "data")
parsed_data_folder = os.path.join('.', "parsed_data")  # stay in current folder
debug = True
