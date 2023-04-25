"""Miscelanneous helper functions."""

import sys
import json


def get_version(filename="VERSION.txt"):
    """Read the program version from VERSION.txt"""
    try:
        with open(filename, "r") as file:
            data = json.load(file)
            version = data["version"]
            return version
    except Exception as e:
        print(f"Could not read version info, bailing out. Something is wrong: {str(e)}")
        sys.exit(-1)
