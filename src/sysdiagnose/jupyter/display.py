#! /usr/bin/env python3

# Sysdiagnose Jupyter display helpers
# Author: EC-DIGIT-CSIRC

"""
Display helpers for sysdiagnose Jupyter integration.

Converts sysdiagnose data structures to pandas DataFrames for rich
rendering in Jupyter notebooks.
"""
import glob
import json
import os

import pandas as pd

from sysdiagnose import Sysdiagnose
from sysdiagnose.utils.logger import logger


def cases_to_df(sd: Sysdiagnose) -> pd.DataFrame:
    """Convert case library to a DataFrame."""
    rows = []
    for case in sd.cases().get_cases().values():
        rows.append({
            'case_id': case.case_id,
            'date': case.case_metadata.get('date', ''),
            'serial_number': case.case_metadata.get('serial_number', ''),
            'unique_device_id': case.case_metadata.get('unique_device_id', ''),
            'ios_version': case.case_metadata.get('ios_version', ''),
            'model': case.case_metadata.get('model', ''),
            'tags': ','.join(case.tags),
        })
    if rows:
        return pd.DataFrame(rows)
    return pd.DataFrame(columns=['case_id', 'date', 'serial_number', 'ios_version', 'model', 'tags'])


def parsers_to_df(sd: Sysdiagnose) -> pd.DataFrame:
    """Convert parser list to a DataFrame."""
    parsers = sd.config.get_parsers()
    return pd.DataFrame([
        {'name': name, 'description': desc}
        for name, desc in parsers.items()
    ])


def analysers_to_df(sd: Sysdiagnose) -> pd.DataFrame:
    """Convert analyser list to a DataFrame."""
    analysers = sd.config.get_analysers()
    return pd.DataFrame([
        {'name': name, 'description': desc}
        for name, desc in analysers.items()
    ])


def case_info_to_df(sd: Sysdiagnose, case_id: str) -> pd.DataFrame:
    """Convert case info to a single-row DataFrame."""
    info = sd.get_case_info(case_id)
    if not info:
        return pd.DataFrame()
    return pd.DataFrame([info])


def result_to_df(parsed_folder: str, name: str) -> pd.DataFrame | None:
    """
    Load a parser/analyser result file as a DataFrame.

    Searches for json/jsonl files matching the name in the parsed_data folder.
    """
    for ext in ['jsonl', 'json']:
        filepath = os.path.join(parsed_folder, f'{name}.{ext}')
        if os.path.isfile(filepath):
            return load_result_file(filepath, ext)

    matches = glob.glob(os.path.join(parsed_folder, f'{name}*'))
    if matches:
        filepath = matches[0]
        ext = filepath.rsplit('.', 1)[-1]
        if ext in ('json', 'jsonl'):
            return load_result_file(filepath, ext)

    logger.warning(f"No result file found for '{name}' in {parsed_folder}")
    return None


def load_result_file(filepath: str, fmt: str) -> pd.DataFrame:
    """Load a json or jsonl file into a DataFrame."""
    if fmt == 'jsonl':
        return _load_jsonl(filepath)
    elif fmt == 'json':
        return _load_json(filepath)
    return pd.DataFrame()


def _load_jsonl(filepath: str) -> pd.DataFrame:
    """Load a JSONL file, flattening nested 'data' dicts into columns."""
    records = []
    with open(filepath, 'r') as f:
        for raw_line in f:
            stripped = raw_line.strip()
            if stripped:
                record = json.loads(stripped)
                records.append(_flatten_event(record))
    df = pd.DataFrame(records)
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce', utc=True)
        df = df.sort_values('datetime').reset_index(drop=True)
    return df


def _load_json(filepath: str) -> pd.DataFrame:
    """Load a JSON file (list or dict) into a DataFrame."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    if isinstance(data, list):
        return pd.json_normalize(data)
    elif isinstance(data, dict):
        return pd.json_normalize([data])
    return pd.DataFrame()


def _flatten_event(record: dict) -> dict:
    """
    Flatten an Event-style record: promote 'data' sub-dict keys
    to top-level with 'data.' prefix to avoid collisions.
    """
    flat = {k: v for k, v in record.items() if k != 'data'}
    data = record.get('data', {})
    if isinstance(data, dict):
        for k, v in data.items():
            flat[f'data.{k}'] = v
    else:
        flat['data'] = data
    return flat
