import glob
import json
import os
import re

from sysdiagnose.utils.base import BaseParserInterface, Event, SysdiagnoseConfig, logger
from sysdiagnose.utils.misc import parse_datetime


class TransparencyParser(BaseParserInterface):
    description = "Parsing transparency.log json file as timeline"
    format = "jsonl"
    ios_version = ">=16.0"

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def is_compatible(self) -> bool:
        version_compatibility = super().is_compatible()
        # not compatible with Apple TV
        device_compatibility = "AppleTV" not in self.case_model and "Watch" not in self.case_model
        # both need to be compatible
        return version_compatibility and device_compatibility

    def get_log_files(self) -> list:
        log_files_globs = [
            "transparency.log",
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            for item in glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)):
                if os.path.getsize(item) > 0:
                    log_files.append(item)

        return log_files

    def execute(self) -> list:
        result = []

        files = self.get_log_files()
        if not files:
            logger.info("No known transparency.log file found.")
            return result

        for fname in files:
            with open(fname) as f:
                try:
                    json_data = json.load(f)
                    result.extend(self.extract_events(json_data))
                except json.decoder.JSONDecodeError:
                    logger.warning(f"Error parsing {fname}")

        return result

    def extract_events(self, json_data: dict) -> list:
        events = []
        for item in json_data.get("registration", []):
            for key in item:
                if "At" in key:
                    # parse the time in this format "2023-04-11 09:38:27 +0000"
                    timestamp = parse_datetime(item[key], "%Y-%m-%d %H:%M:%S %z")
                    event = Event(
                        datetime=timestamp,
                        message=f"Transparency: registration app {item.get('app')} {key}",
                        module=self.module_name,
                        timestamp_desc="app registration",
                    )
                    events.append(event.to_dict())
        sm = json_data.get("stateMachine")
        if sm:
            try:
                key = "accountFirstSeen"
                timestamp = parse_datetime(sm[key], "%Y-%m-%d %H:%M:%S %z")
                event = Event(
                    datetime=timestamp,
                    message=f"Transparency: stateMachine {key}",
                    module=self.module_name,
                    timestamp_desc="stateMachine",
                )
                events.append(event.to_dict())
            except KeyError:
                pass
            try:
                key = "backgroundOp lastDutyCycle"
                timestamp = parse_datetime(sm["backgroundOp"]["lastDutyCycle"], "%Y-%m-%dT%H:%M:%SZ")
                event = Event(
                    datetime=timestamp,
                    message=f"Transparency: stateMachine {key}",
                    module=self.module_name,
                    timestamp_desc="stateMachine",
                )
                events.append(event.to_dict())
            except KeyError:
                pass
            try:
                key = "backgroundOp lastSuccess"
                timestamp = parse_datetime(sm["backgroundOp"]["lastSuccess"], "%Y-%m-%dT%H:%M:%SZ")
                event = Event(
                    datetime=timestamp,
                    message=f"Transparency: stateMachine {key}",
                    module=self.module_name,
                    timestamp_desc="stateMachine",
                )
                events.append(event.to_dict())
            except KeyError:
                pass

            for key, t in sm.get("lasts", {}).items():
                timestamp = parse_datetime(t, "%Y-%m-%d %H:%M:%S %z")
                event = Event(
                    datetime=timestamp,
                    message=f"Transparency: stateMachine last {key}",
                    module=self.module_name,
                    timestamp_desc="stateMachine",
                )
                events.append(event.to_dict())

            for launch in sm.get("launch", []):
                t, key = launch.split(" - ")
                # parse the time in this format 2024-08-19T09:00:28.946+0200
                timestamp = parse_datetime(t, "%Y-%m-%dT%H:%M:%S.%f%z")
                event = Event(
                    datetime=timestamp,
                    message=f"Transparency: stateMachine launch {key}",
                    module=self.module_name,
                    timestamp_desc="stateMachine",
                )
                events.append(event.to_dict())

            try:
                key = "lockstate"
                # extract the time from the string using regex "foobar 2024-08-19 09:00:28 +0200"
                time_str = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4}", sm[key]).group(0)
                timestamp = parse_datetime(time_str, "%Y-%m-%d %H:%M:%S %z")
                event = Event(
                    datetime=timestamp,
                    message=f"Transparency: stateMachine {key}",
                    module=self.module_name,
                    timestamp_desc="stateMachine",
                )
                events.append(event.to_dict())
            except AttributeError:
                # lockstate may not contain timestamp
                pass
            except KeyError:
                # log may not contain lockstate entry
                pass

            for _key, val in sm.get("ops", {}).items():
                try:
                    time_str = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4})", val).group(0)
                    timestamp = parse_datetime(time_str, "%Y-%m-%d %H:%M:%S %z")
                    event = Event(
                        datetime=timestamp,
                        message=f"Transparency: stateMachine ops {val}",
                        module=self.module_name,
                        timestamp_desc="stateMachine",
                    )
                    events.append(event.to_dict())
                except AttributeError:
                    # value does not contain a timestamp
                    pass
        return events
