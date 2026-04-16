#! /usr/bin/env python
#
# For Python3
# Function to handle different types of times

from datetime import datetime, UTC


def macepoch2time(macepoch):
    # convert install_date from Cocoa EPOCH -> UTC
    epoch = macepoch + 978307200  # difference between COCOA and UNIX epoch is 978307200 seconds
    utctime = datetime.fromtimestamp(epoch, tz=UTC)
    return utctime


# --------------------------------------------------------------------------- #
# That's all folks ;)
