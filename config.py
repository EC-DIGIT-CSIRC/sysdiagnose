import os

"""
This file contains all of the configuration values for the project.
"""


config_folder = os.path.dirname(os.path.abspath(__file__))

cases_file = os.path.join('.', "cases.json")
data_folder = os.path.join('.', "data")
parsed_data_folder = os.path.join('.', "parsed_data")  # stay in current folder
parsers_folder = os.path.join('.', "parsers")
analysers_folder = os.path.join('.', "analysers")
debug = True
