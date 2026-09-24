import importlib
import json
import os
from collections.abc import Generator

from sysdiagnose.utils.base import (
    BaseAnalyserInterface,
    BaseInterface,
    BaseParserInterface,
    SysdiagnoseConfig,
    logger,
)


class TimesketchAnalyser(BaseAnalyserInterface):
    description = "Aggregate every timeline-producing parser and analyser into one Timesketch-compatible JSONL."
    format = "jsonl"

    def __init__(self, config: SysdiagnoseConfig, case: dict) -> None:
        super().__init__(__file__, config, case)

    def execute(self) -> Generator[dict, None, None]:
        yield from self._collect(self.config.get_parsers(), "sysdiagnose.parsers", BaseParserInterface)
        yield from self._collect(self.config.get_analysers(), "sysdiagnose.analysers", BaseAnalyserInterface)

    def _collect(
        self, modules: dict, package: str, base_cls: type
    ) -> Generator[dict, None, None]:
        for name in modules:
            if name == self.module_name:
                continue

            cls = self._load_class(package, name, base_cls)
            if cls is None:
                continue

            try:
                instance: BaseInterface = cls(config=self.config, case=self.case)
            except Exception:
                logger.exception(f"Failed to instantiate {package}.{name}")
                continue

            if not instance.contains_timestamp():
                continue

            if not instance.is_compatible():
                logger.info(
                    f"Skipping {name}: not compatible with iOS {self.case_ios_version} (requires {instance.ios_version})"
                )
                continue

            # Prefer the on-disk jsonl over get_result(): reading from cache avoids
            # materialising millions of events per parser in memory.
            if not instance.output_exists():
                try:
                    instance.save_result()
                except Exception:
                    logger.exception(f"Failed to run {name}")
                    continue

            if not os.path.exists(instance.output_file):
                continue

            data_type = f"sysdiagnose:{name}"
            try:
                with open(instance.output_file, encoding="utf-8") as f:
                    for raw in f:
                        raw = raw.strip()
                        if not raw:
                            continue
                        try:
                            entry = json.loads(raw)
                        except json.JSONDecodeError:
                            logger.warning(f"Skipping malformed line in {name}")
                            continue
                        enriched = self._to_timesketch_event(entry, name, data_type)
                        if enriched is not None:
                            yield enriched
            except OSError:
                logger.exception(f"Failed to read output of {name}")

    @staticmethod
    def _load_class(package: str, name: str, base_cls: type) -> type | None:
        try:
            module = importlib.import_module(f"{package}.{name}")
        except Exception:
            logger.exception(f"Failed to import {package}.{name}")
            return None

        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, base_cls) and obj is not base_cls:
                return obj
        return None

    @staticmethod
    def _to_timesketch_event(entry: dict, source_name: str, data_type: str) -> dict | None:
        if not isinstance(entry, dict) or "datetime" not in entry:
            return None

        enriched = dict(entry)
        enriched.setdefault("data_type", data_type)
        if not enriched.get("timestamp_desc"):
            enriched["timestamp_desc"] = source_name
        if not enriched.get("message"):
            enriched["message"] = f"{source_name} event"
        return enriched

    def _write_result(self, result, indent=None) -> int:
        # Override to avoid the base class materialising the generator into memory
        # (see the FIXME in BaseInterface._write_result). We stream each event to
        # disk and drop it — get_result() would still work by re-reading the file.
        num_events = 0
        with open(self.output_file, "w") as f:
            for line in result:
                f.write(json.dumps(line, ensure_ascii=False, indent=indent))
                f.write("\n")
                num_events += 1
        self._result = None
        return num_events
