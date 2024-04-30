"""Miscelanneous helper functions."""

import os
import sys
import json
import plistlib
from datetime import datetime
import binascii


def get_version(filename="VERSION.txt"):
    """Read the program version from VERSION.txt"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(script_dir)
        version_file = os.path.join(script_dir, filename)
        with open(version_file, "r") as file:
            data = json.load(file)
            version = data["version"]
            return version
    except Exception as e:
        print(f"Could not read version info, bailing out. Something is wrong: {str(e)}")
        sys.exit(-1)


def load_plist_as_json(fname: str):
    with open(fname, 'rb') as f:
        plist = plistlib.load(f)
        return plist


def find_datetime(d):
    for k, v in d.items():
        if isinstance(v, dict):
            find_datetime(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    find_datetime(item)
        elif isinstance(v, datetime.datetime):
            d[k] = v.isoformat()
    return d


def find_bytes(d):
    for k, v in d.items():
        if isinstance(v, dict):
            find_bytes(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    find_bytes(item)
        elif isinstance(v, bytes):
            # not sure about that but it fixes the issue
            # encoding is not always utf-8
            d[k] = binascii.hexlify(v).decode('utf-8')
    return d
