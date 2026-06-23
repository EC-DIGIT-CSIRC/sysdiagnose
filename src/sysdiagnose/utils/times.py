import unicodedata
from datetime import UTC, datetime

# Precompute translation table for all Unicode decimal digits → ASCII
_DIGIT_TABLE = {}
for i in range(0x110000):
    ch = chr(i)
    d = unicodedata.decimal(ch, None)
    if d is not None and i > 127:
        _DIGIT_TABLE[i] = ord("0") + d


def parse_datetime(s: str, fmt: str | None = None) -> datetime:
    """Parse a datetime string, normalizing non-ASCII digits first."""
    normalized = s.translate(_DIGIT_TABLE)
    if fmt:
        return datetime.strptime(normalized, fmt)
    return datetime.fromisoformat(normalized)


def macepoch2time(macepoch: float) -> datetime:
    # convert install_date from Cocoa EPOCH -> UTC
    epoch = macepoch + 978307200  # difference between COCOA and UNIX epoch is 978307200 seconds
    utctime = datetime.fromtimestamp(epoch, tz=UTC)
    return utctime
