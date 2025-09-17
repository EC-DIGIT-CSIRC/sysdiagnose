import re
from enum import Enum

class DataType(Enum):
    XML_LIKE = 1
    LIST = 2


def parse_list(input_string: str):
    input = re.search(r'\((.+,.+)\)', input_string).group(1)
    list_of_elements = input.split(',')
    res = []

    for element in list_of_elements:
        res.append(element.strip())

    return res


def parse_xml_like(input_string: str):
    input = re.search(r'<(.+)>', input_string).group(1)
    list_of_elements = input.split(',')
    res = {}

    for element in list_of_elements:
        element = element.strip()
        key = element.split(' ', 1)[0]
        value = element.split(' ', 1)[1]
        # TODO check key uniqueness
        res[key] = value

    return res

def detect_type(input: str) -> DataType:
    if re.search(r'<.+>', input):
        return DataType.XML_LIKE

    if re.search(r'\(.+,.+\)', input):
        return DataType.LIST

def parse(input_string: str):
    input_string = input_string.strip()
    type = detect_type(input_string)

    match type:
        case DataType.XML_LIKE:
            parse_xml_like(input_string)

        case DataType.LIST:
            parse_list(input_string)

        case _:
            print('not found')


test_1 = '<class IORegistryEntry, id 0x100000100, retain 52>'
test_2 = '<class IORegistryEntry:IOService:IOPlatformExpertDevice, id 0x1000001cf, registered, matched, active, busy 0 (10227 ms), retain 29>'
test_3 = '<class IORegistryEntry:IOService:IODTNVRAM, id 0x10000010e, registered, matched, active, busy 0 (158 ms), retain 11>'
test_4 = '<class IORegistryEntry:IOService:IODTNVRAMDiags, id 0x1000001d0, registered, matched, active, busy 0 (33 ms), retain 6>'
test_5 = '<class IORegistryEntry, id <0x100000, 0x200000>, retain 52>'
test_6 = '<key: value, id idval, mykey: (myval, myval2), otherkey (otherval, otherval2)>'

parse(test_5)
