"""Miscelanneous helper functions."""

import os
import sys
import json
import plistlib
from datetime import datetime
import binascii
from functools import singledispatch


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
        return json_serializable(plist)


# https://stackoverflow.com/questions/51674222/how-to-make-json-dumps-in-python-ignore-a-non-serializable-field
_cant_serialize = object()


@singledispatch
def json_serializable(object, skip_underscore=False):
    """Filter a Python object to only include serializable object types

    In dictionaries, keys are converted to strings; if skip_underscore is true
    then keys starting with an underscore ("_") are skipped.

    """
    # default handler, called for anything without a specific
    # type registration.
    return _cant_serialize


@json_serializable.register(dict)
def _handle_dict(d, skip_underscore=False):
    converted = ((str(k), json_serializable(v, skip_underscore))
                 for k, v in d.items())
    if skip_underscore:
        converted = ((k, v) for k, v in converted if k[:1] != '_')
    return {k: v for k, v in converted if v is not _cant_serialize}


@json_serializable.register(list)
@json_serializable.register(tuple)
def _handle_sequence(seq, skip_underscore=False):
    converted = (json_serializable(v, skip_underscore) for v in seq)
    return [v for v in converted if v is not _cant_serialize]


@json_serializable.register(int)
@json_serializable.register(float)
@json_serializable.register(str)
@json_serializable.register(bool)  # redudant, supported as int subclass
@json_serializable.register(type(None))
def _handle_default_scalar_types(value, skip_underscore=False):
    return value


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
