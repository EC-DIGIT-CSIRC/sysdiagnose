import re
import io
import sysdiagnose.utils.misc as misc
from datetime import datetime, timezone


def extract_from_file(fname):
    with open(fname, 'r', encoding="utf-8") as f:
        return extract_from_iowrapper(f)


def extract_from_string(logstring):
    return extract_from_iowrapper(io.StringIO(logstring))


def extract_from_iowrapper(f: io.TextIOWrapper):
    # multiline parsing with the following logic:
    # - build an entry with the seen lines
    # - upon discovery of a new entry, or the end of the file, consider the entry as complete and process the lines
    # - discovery of a new entry is done based on the timestamp, as each new entry starts this way
    events = []
    prev_lines = []
    kv_section = False  # key-value section separated by a semicolon
    for line in f:
        timeregex = re.search(r"(?<=^)(.*?)(?= \[[0-9]+)", line)  # Regex for timestamp
        if '_____' in line and re.search(r": _{10,25} [^_]+ _{10,25}", line):
            kv_section = 'start'
        if timeregex and (not kv_section or kv_section == 'start' or kv_section == 'end'):
            # new entry, process the previous entry
            if kv_section == 'start':
                kv_section = True
            if kv_section == 'end':
                kv_section = False
                events.append(build_from_kv_section(prev_lines))
                prev_lines = []
                continue  # go to next line as current line is just the closure of the section
            elif prev_lines:
                new_entry = build_from_logentry(''.join(prev_lines))
                events.append(new_entry)
            # build the new entry
            prev_lines = []
            prev_lines.append(line)
        elif prev_lines or kv_section:
            # not a new entry, add the line to the previous entry
            prev_lines.append(line)
        else:
            pass
        if kv_section and '_____' in line and re.search(r": _{40,80}$", line):  # only end if kv_section was started
            kv_section = 'end'
    # process the last entry
    if kv_section and len(prev_lines) > 1:
        new_entry = build_from_kv_section(prev_lines)
    else:
        new_entry = build_from_logentry(''.join(prev_lines))
    if new_entry:
        events.append(new_entry)
    return events


def build_from_kv_section(lines):
    new_entry = build_from_logentry(lines.pop(0))  # first line is a normal line
    if '_____' in lines[-1]:
        lines.pop()  # drop last line as it's just the closing line
    # complement with key-value section
    for line in lines:
        splitted = line.split(":")
        if len(splitted) > 1:
            new_entry[splitted[-2].strip()] = splitted[-1].strip()
    return new_entry


def build_from_logentry(line):
    entry = {}
    # timestamp
    timeregex = re.search(r"(?<=^)(.*?)(?= \[[0-9]+)", line)  # Regex for timestamp
    if timeregex:
        timestamp_str = timeregex.group(1)
        timestamp = datetime.strptime(timestamp_str, "%a %b %d %H:%M:%S %Y")
        timestamp = timestamp.replace(tzinfo=timezone.utc)
        entry['timestamp'] = timestamp.timestamp()
        entry['datetime'] = timestamp.isoformat(timespec='microseconds')

        # log level
        loglevelregex = re.search(r"\<(.*?)\>", line)
        entry['loglevel'] = loglevelregex.group(1)

        # hex_ID
        hexIDregex = re.search(r"\(0x(.*?)\)", line)
        entry['hexID'] = '0x' + hexIDregex.group(1)

        # event_type
        eventyperegex = re.search(r"\-\[(.*)(\]\:)", line)
        if eventyperegex:
            entry['event_type'] = eventyperegex.group(1)

        # msg
        if 'event_type' in entry:
            msgregex = re.search(r"\]\:(.*)", line, re.MULTILINE | re.DOTALL)
        else:
            msgregex = re.search(r"\)\ (.*)", line, re.MULTILINE | re.DOTALL)
        line = msgregex.group(1).strip()
        # plist parsing
        if line.endswith('</plist>'):
            plist_start = line.index('<?xml version')
            entry['msg'] = line[:plist_start].strip()
            plist_data = line[plist_start:]
            entry['plist'] = misc.load_plist_string_as_json(plist_data)
            # LATER parse the plist content
            # - extract the recursive plist
            # - decode the certificates into nice JSON
            # - and so on with more fun for the future
        else:
            entry['msg'] = msgregex.group(1).strip()

    return entry


# function copied from https://github.com/abrignoni/iOS-Mobile-Installation-Logs-Parser/blob/master/mib_parser.sql.py
# Month to numeric with leading zero when month < 10 function
# Function call: month = month_converter(month)


def month_converter(month):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month = months.index(month) + 1
    if (month < 10):
        month = f"{month:02d}"
    return month

# Day with leading zero if day < 10 function
# Functtion call: day = day_converter(day)


def day_converter(day):
    day = int(day)
    if (day < 10):
        day = f"{day:02d}"
    return day
##
