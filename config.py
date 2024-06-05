import os

"""
This file contains all of the configuration values for the project.
"""


config_folder = os.path.dirname(os.path.abspath(__file__))

cases_file = os.path.join(os.curdir, "cases.json")
data_folder = os.path.join(config_folder, "data")
parsed_data_folder = os.path.join(os.curdir, "parsed_data")  # stay in current folder
parsers_folder = os.path.join(config_folder, "parsers")
analysers_folder = os.path.join(config_folder, "analysers")
debug = True
