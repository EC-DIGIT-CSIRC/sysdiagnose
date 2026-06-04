import json
import logging
import os
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime as datetime_datetime
from enum import StrEnum

logger = logging.getLogger("sysdiagnose")


class ExecutionStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ResultSummary:
    """
    Class that represents a summary of the invocation of a BaseParserInterface or BaseAnalyserInterface subclass.

    The summary includes the status of the execution (e.g. OK, WARNING, ERROR), the execution timing metadata,
    and the number of errors, warnings, and events that were encountered during the execution.

    By default, the status is set to ERROR, the timing metadata is unknown, and the number of errors, warnings,
    and events are set to 0.
    """

    status: ExecutionStatus = ExecutionStatus.ERROR
    start_time: datetime_datetime | None = None
    duration: float | None = None
    num_errors: int = 0
    num_warnings: int = 0
    num_events: int = 0

    def to_dict(self) -> dict:
        start_time = None
        if self.start_time is not None:
            start_time = self.start_time.astimezone(UTC).isoformat(timespec="microseconds")
        return {
            "status": self.status.value,
            "start_time": start_time,
            "duration": self.duration,
            "num_errors": self.num_errors,
            "num_warnings": self.num_warnings,
            "num_events": self.num_events,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResultSummary":
        status = data.get("status", ExecutionStatus.ERROR)
        start_time = data.get("start_time")
        if start_time is not None:
            start_time = datetime_datetime.fromisoformat(start_time).astimezone(UTC)
        return cls(
            status=ExecutionStatus(status),
            start_time=start_time,
            duration=data.get("duration"),
            num_errors=data.get("num_errors", 0),
            num_warnings=data.get("num_warnings", 0),
            num_events=data.get("num_events", 0),
        )


class ResultSummaryLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.num_errors = 0
        self.num_warnings = 0

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            self.num_errors += 1
        elif record.levelno >= logging.WARNING:
            self.num_warnings += 1


class ResultSummaryFactory:
    @staticmethod
    def from_result(result: list | dict | str | None) -> ResultSummary:
        num_errors = ResultSummaryFactory.count_errors_in_result(result)
        num_events = ResultSummaryFactory.count_events_in_result(result)
        return ResultSummary(
            status=ResultSummaryFactory.get_execution_status(num_errors=num_errors, num_warnings=0),
            num_errors=num_errors,
            num_events=num_events,
        )

    @staticmethod
    def from_output(output_file: str, format_name: str) -> ResultSummary:
        """
        Creates a ResultSummary object from an output file.
        :param output_file: The path to the output file.
        :param format_name: The format of the output file (e.g. "json", "jsonl").
        :return: A ResultSummary object containing the summary of the output file.
        """
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            return ResultSummary()

        with open(output_file) as f:
            if format_name == "json":
                loaded_result = json.load(f)
            elif format_name == "jsonl":
                num_events = sum(1 for line in f if line.strip())
                return ResultSummary(status=ExecutionStatus.OK, num_events=num_events)
            else:
                loaded_result = f.read()
        return ResultSummaryFactory.from_result(loaded_result)

    @staticmethod
    def get_execution_status(num_errors: int, num_warnings: int) -> ExecutionStatus:
        if num_errors > 0:
            return ExecutionStatus.ERROR
        if num_warnings > 0:
            return ExecutionStatus.WARNING
        return ExecutionStatus.OK

    @staticmethod
    def count_events_in_result(result: list | dict | str | None) -> int:
        if result is None:
            return 0
        if isinstance(result, list):
            return len(result)
        return 1 if result else 0

    @staticmethod
    def count_errors_in_result(result: list | dict | str | None) -> int:
        if not isinstance(result, dict):
            return 0

        num_errors = 0
        if ResultSummaryFactory.has_error_value(result.get("error")):
            num_errors += ResultSummaryFactory.count_error_value(result.get("error"))
        if ResultSummaryFactory.has_error_value(result.get("errors")):
            num_errors += ResultSummaryFactory.count_error_value(result.get("errors"))
        return num_errors

    @staticmethod
    def has_error_value(value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, list | tuple | set | dict | str):
            return len(value) > 0
        return bool(value)

    @staticmethod
    def count_error_value(value: object) -> int:
        if isinstance(value, dict):
            return len(value)
        if isinstance(value, list | tuple | set):
            return len(value)
        if value:
            return 1
        return 0


class ResultSummaryExecutionHandler:
    """
    Manages the lifecycle of a ResultSummary during execution.
    Provides start/update/get semantics with log handler integration.
    """

    def __init__(self) -> None:
        self._summary: ResultSummary | None = None
        self._log_handler: ResultSummaryLogHandler | None = None
        self._start_time: datetime_datetime | None = None
        self._finalized: bool = False

    def start(self) -> None:
        """Initialises the ResultSummary and attaches the log handler."""
        self._start_time = datetime_datetime.now(UTC)
        self._log_handler = ResultSummaryLogHandler()
        self._summary = ResultSummary(start_time=self._start_time)
        self._finalized = False
        logger.addHandler(self._log_handler)

    def update(self, num_events: int = 0, add_errors: int = 0, add_warnings: int = 0, end: bool = False) -> None:
        """
        Updates the summary with event count and additional errors/warnings.

        Args:
            num_events: Sets the number of events in the summary.
            add_errors: Additional errors to add (on top of those captured by the log handler).
            add_warnings: Additional warnings to add (on top of those captured by the log handler).
            end: If True, finalizes the summary by setting the duration and detaching the log handler.
        """
        if self._summary is None:
            logger.warning("ResultSummaryExecutionHandler.update() called before start(), calling start() implicitly.")
            self.start()

        self._summary.num_events = num_events
        self._summary.num_errors = self._log_handler.num_errors + add_errors
        self._summary.num_warnings = self._log_handler.num_warnings + add_warnings
        self._summary.status = ResultSummaryFactory.get_execution_status(
            self._summary.num_errors, self._summary.num_warnings
        )

        if end:
            self._finalize()

    def get(self) -> ResultSummary:
        """Returns the finalized ResultSummary. Finalizes implicitly if not already done."""
        if not self._finalized:
            logger.warning("ResultSummaryExecutionHandler.get() called before finalization, finalizing implicitly.")
            self._finalize()
        return self._summary

    def _finalize(self) -> None:
        """Sets duration, detaches log handler, and marks as finalized."""
        if self._finalized:
            return
        self._summary.duration = (datetime_datetime.now(UTC) - self._start_time).total_seconds()
        logger.removeHandler(self._log_handler)
        self._finalized = True
