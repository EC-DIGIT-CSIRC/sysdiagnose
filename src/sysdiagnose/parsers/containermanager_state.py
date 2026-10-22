#! /usr/bin/env python3
"""
Parser for the iOS 27 ``logs/ContainerManager/state.json`` file.

From iOS 27 the container manager daemon state is written as JSON in ``logs/ContainerManager/`` and the
text logs read by the ``containermanager`` and ``appinstallation`` parsers are no longer shipped.
The JSON describes the app data, app group, extension (plugin) and system containers the daemon knows
about, with directory timestamps, plus the extension-to-app map and a code-signing registration cache.

Every row is evidence of what the daemon knew when the snapshot was taken. A container record with
timestamps shows that a container directory existed; a record without a node shows that none existed
at that time. Neither is proof of use, installation or removal by the user.
"""

import os
from datetime import datetime

from sysdiagnose.utils.base import BaseParserInterface, Event, SysdiagnoseConfig, logger
from sysdiagnose.utils.container_state import COLUMNS, parse_state_bytes

STATE_FILE = "logs/ContainerManager/state.json"

_DESCRIPTIONS = {
    "container": "Container record",
    "codesign": "Code-signing registration",
    "child_parent": "Extension to app mapping",
    "client": "Container manager client",
    "class_path": "Container class directory",
    "persona": "Persona identity",
    "managed_path": "Managed path",
    "unknown_section": "Unrecognised section",
}


class ContainerManagerStateParser(BaseParserInterface):
    description = "Parsing the iOS 27 ContainerManager state.json file (app, group and extension containers)"
    format = "jsonl"
    ios_version = ">=27.0"

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def get_log_files(self) -> list:
        path = os.path.join(self.case_data_subfolder, STATE_FILE)
        return [path] if os.path.isfile(path) else []

    @staticmethod
    def _message(row: dict) -> str:
        label = _DESCRIPTIONS.get(row["record_type"], row["record_type"])
        parts = [label]
        if row["container_class"]:
            parts.append(f"({row['container_class']})")
        if row["identifier"]:
            parts.append(row["identifier"])
        if row["parent_identifier"]:
            parts.append(f"-> {row['parent_identifier']}")
        if row["state"]:
            parts.append(f"[{row['state']}]")
        return " ".join(parts)

    def execute(self) -> list:
        log_files = self.get_log_files()
        if not log_files:
            logger.warning(f"No {STATE_FILE} file present (it is only written by iOS 27 and later)")
            return []

        fallback = self.sysdiagnose_creation_datetime
        result = []
        for log_file in log_files:
            try:
                with open(log_file, "rb") as handle:
                    raw = handle.read()
            except OSError as exc:
                logger.warning(f"Cannot read {log_file}: {exc}")
                continue
            rows = parse_state_bytes(raw, source_file=STATE_FILE, warn=logger.warning)
            for row in rows:
                if row["timestamp_utc"]:
                    stamp = datetime.fromisoformat(row["timestamp_utc"].replace("Z", "+00:00"))
                    desc = row["timestamp_desc"]
                else:
                    stamp = fallback
                    desc = "sysdiagnose creation time (record carries no timestamp)"
                data = {column: row[column] for column in COLUMNS if row[column] not in ("", None)}
                event = Event(
                    datetime=stamp,
                    message=self._message(row),
                    module=self.module_name,
                    timestamp_desc=desc,
                    data=data,
                )
                result.append(event.to_dict())
        return result
