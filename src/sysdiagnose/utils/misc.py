"""Miscelanneous helper functions."""

from datetime import datetime
from functools import singledispatch
from pathlib import Path
import base64
import binascii
import json
import nska_deserialize
import os
import re
from collections.abc import MutableMapping


def merge_dicts(a: dict, b: dict) -> dict:
    for key, value in b.items():
        if key in a:
            if isinstance(value, dict):
                a[key] = merge_dicts(a[key], value)
            elif isinstance(value, list):
                a[key].extend(value)
            else:
                a[key] = value
        else:
            a[key] = value
    return a


def get_version(filename="VERSION.txt"):
    """Read the program version from VERSION.txt"""
    try:
        script_dir = Path(__file__).parent.parent
        version_file = os.path.join(script_dir, filename)
        with open(version_file, "r") as file:
            data = json.load(file)
            version = data["version"]
            return version
    except Exception as e:
        exit(f"Could not read version info, bailing out. Something is wrong: {str(e)}")


def load_plist_file_as_json(fname: str) -> dict:
    if os.path.getsize(fname) == 0:
        return {'error': ['Empty file']}
    try:
        with open(fname, 'rb') as f:
            plist = nska_deserialize.deserialize_plist(f, full_recurse_convert_nska=True, format=dict)
            return json_serializable(plist)
    except Exception:
        return {'error': ['Invalid plist file']}


def load_plist_string_as_json(plist_string: str) -> dict:
    plist = nska_deserialize.deserialize_plist_from_string(plist_string.encode(), full_recurse_convert_nska=True, format=dict)
    return json_serializable(plist)


def load_plist_bytes_as_json(plist_bytes: bytes) -> dict:
    plist = nska_deserialize.deserialize_plist_from_string(plist_bytes, full_recurse_convert_nska=True, format=dict)
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


@json_serializable.register(bytes)
def _handle_bytes(value, skip_underscore=False):
    try:
        return value.decode(errors='strict')
    except Exception:
        return base64.b64encode(value).decode(errors='ignore')


@json_serializable.register(datetime)
def _handle_datetime(value, skip_underscore=False):
    return value.isoformat(timespec='microseconds')


def find_datetime(d):
    for k, v in d.items():
        if isinstance(v, dict):
            find_datetime(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    find_datetime(item)
        elif isinstance(v, datetime.datetime):
            d[k] = v.isoformat(timespec='microseconds')
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


def snake_case(s):
    # lowercase and replace non a-z characters as _
    return re.sub(r'[^a-zA-Z0-9%]', '_', s.lower())


# https://www.freecodecamp.org/news/how-to-flatten-a-dictionary-in-python-in-4-different-ways/
def _flatten_dict_gen(d, parent_key, sep):
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            yield from flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v


def flatten_dict(d: MutableMapping, parent_key: str = '', sep: str = '.'):
    return dict(_flatten_dict_gen(d, parent_key, sep))
