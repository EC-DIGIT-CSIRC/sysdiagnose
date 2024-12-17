"""Miscelanneous helper functions."""

from datetime import datetime
from functools import singledispatch
from pathlib import Path
import base64
import binascii
import json
import nska_deserialize
import os
import heapq


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


def sort_large_file(input_file, output_file, chunk_size=100000):
    temp_files = []

    try:
        # Step 1: Split into sorted chunks
        with open(input_file, "r") as infile:
            chunk = []
            for line in infile:
                record = json.loads(line.strip())
                chunk.append(record)

                # When chunk size is reached, sort and write to a temporary file
                if len(chunk) >= chunk_size:
                    temp_file = f"temp_chunk_{len(temp_files)}.jsonl"
                    with open(temp_file, "w") as tmp:
                        for record in sorted(chunk, key=lambda x: x["timestamp"]):
                            tmp.write(json.dumps(record) + "\n")
                    temp_files.append(temp_file)
                    chunk = []

            # Sort and write any remaining records
            if chunk:
                temp_file = f"temp_chunk_{len(temp_files)}.jsonl"
                with open(temp_file, "w") as tmp:
                    for record in sorted(chunk, key=lambda x: x["timestamp"]):
                        tmp.write(json.dumps(record) + "\n")
                temp_files.append(temp_file)

        # Step 2: Merge sorted chunks
        with open(output_file, "w") as outfile:
            open_files = [open(temp_file, "r") for temp_file in temp_files]
            iterators = (map(json.loads, f) for f in open_files)
            for record in heapq.merge(*iterators, key=lambda x: x["timestamp"]):
                outfile.write(json.dumps(record) + "\n")
    finally:
        # Close all temporary files
        for f in open_files:
            f.close()
        for f in temp_files:
            os.remove(f)