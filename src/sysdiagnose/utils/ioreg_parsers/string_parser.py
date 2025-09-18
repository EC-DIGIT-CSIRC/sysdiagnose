import re
from enum import Enum
from sysdiagnose.utils.base import logger
import uuid

class DataType(Enum):
    XML_LIKE = 1
    LIST = 2
    UNKNOWN = 3

class Detect:
    _best_len = float('inf')
    _best_type = DataType.UNKNOWN
    _best_whole = ""      # whole match, for example : <data1, data2>
    _best_content = ""    # content, for example : data1, data2
    _found = False

    def __init__(self, input_string: str):
        self.detect_type(input_string)

    def detect_type(self, input: str):
        # find the smallest
        hit = re.search(r'<((?!.*<.*).*?)>', input)
        if hit and len(hit.group(0)) < self._best_len:
            self.assign_best(hit, DataType.XML_LIKE)

        # find the smallest
        hit = re.search(r'\(((?!.*\(.*).+?,.+?)\)', input)
        if hit and len(hit.group(0)) < self._best_len:
            self.assign_best(hit, DataType.LIST)

    def assign_best(self, hit: re.Match, type: DataType):
        self._best_len = len(hit.group(0))
        self._best_type = type
        self._best_whole = hit.group(0)
        self._best_content = hit.group(1)
        self._found = True

    @property
    def len(self) -> int:
        return self._best_len

    @property
    def type(self) -> DataType:
        return self._best_type

    @property
    def whole_match(self) -> str:
        return self._best_whole

    @property
    def content(self) -> str:
        return self._best_content

    @property
    def found(self) -> bool:
        return self._found


def generate_tag() -> str:
    return str(uuid.uuid4())


def check_anomaly(s: str, tag: str):
    diff = s.replace(tag, '')

    if tag in s and diff:
        logger.warning("Warning : Anomaly: some data was right next to "
                       "the struct (without space), this data is thus lost\n---> " + diff)


def check_key_uniqueness(dictio: dict, key: str):
    if dictio.get(key):
        logger.warning('Warning : Key is already in dictionary, data may be lost\n---> ' + key)


def parse_list(input_string: str) -> list:
    list_of_elements = input_string.split(',')
    res = []

    for element in list_of_elements:
        res.append(element.strip())

    return res


def parse_xml_like(input_string: str) -> dict:
    list_of_elements = input_string.split(',')
    res = {}

    for element in list_of_elements:
        element = element.strip()
        key = element.split(' ', 1)[0]
        value = element.split(' ', 1)[1]
        check_key_uniqueness(res, key)
        res[key] = value

    return res


def parse_type(input_string: str, type: DataType):
    match type:
        case DataType.XML_LIKE:
            return parse_xml_like(input_string)

        case DataType.LIST:
            return parse_list(input_string)

        case _:
            print('not found')


def resolve_tag_dict(final_struct: dict, tag: str, constructed: dict | list):
    for key in final_struct:
        elem = final_struct[key]

        if isinstance(elem, str) and tag in elem:
            check_anomaly(elem, tag)
            final_struct[key] = constructed
            return True

        elif isinstance(elem, list):
            if resolve_tag_list(elem, tag, constructed):
                return True

    return False


def resolve_tag_list(final_struct: list, tag: str, constructed: dict | list):
    for i in range(len(final_struct)):
        elem = final_struct[i]

        if isinstance(elem, str) and tag in elem:
            check_anomaly(elem, tag)
            final_struct[i] = constructed
            return True

        elif isinstance(elem, dict):
            if resolve_tag_dict(elem, tag, constructed):
                return True

    return False


def resolve_tag(final_struct: dict | list, tag: str, constructed: dict | list):
    if isinstance(final_struct, dict):
        resolve_tag_dict(final_struct, tag, constructed)

    elif isinstance(final_struct, list):
        resolve_tag_list(final_struct, tag, constructed)

    else:
        logger.error('Error : struct type not found')
        exit(1)


def parse(data_string: str):
    data_string = data_string.strip()
    hit = Detect(data_string)
    final_struct = None

    # recursion stop
    if not hit.found:
        return None

    # form basic struct
    constructed = parse_type(hit.content, hit.type)

    # replace struct by an unique tag
    tag = generate_tag()
    data_string = data_string.replace(hit.whole_match, tag)

    # recursion
    final_struct = parse(data_string)

    # reconstruct data structure
    if not final_struct:
        final_struct = constructed      # at the root
    else:
        resolve_tag(final_struct, tag, constructed)

    return final_struct


test_1 = '<class IORegistryEntry, id 0x100000100, retain 52>'
test_2 = '<class IORegistryEntry:IOService:IOPlatformExpertDevice, id 0x1000001cf, registered, matched, active, busy 0 (10227 ms), retain 29>'
test_3 = '<class IORegistryEntry:IOService:IODTNVRAM, id 0x10000010e, registered, matched, active, busy 0 (158 ms), retain 11>'
test_4 = '<class IORegistryEntry:IOService:IODTNVRAMDiags, id 0x1000001d0, registered, matched, active, busy 0 (33 ms), retain 6>'
test_5 = '<class IORegistryEntry, id (0x100000, 0x200000), retain 52>'
test_6 = '<class IORegistryEntry, id (0x100000, 0x200000, <key1 val1 , key2 val2,key3 (li1,li2 , li3, li4)>, 0x300000), retain 52>'
test_7 = '<class IORegistryEntry, id <0x100000, 0x200000>, user <alec, gilles>, retain 52>'
test_8 = '<key: value, id idval, mykey: (myval, < k1 v1, k2 v2 >), otherkey (otherval, otherval2)>'

print(parse(test_8))
