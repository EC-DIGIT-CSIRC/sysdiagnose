import re
from enum import Enum
from sysdiagnose.utils.base import logger
import uuid

class DataType(Enum):
    XML_LIKE = 1
    LIST = 2
    UNKNOWN = 3

class Detect:
    _best_len = 0
    _best_type = DataType.UNKNOWN
    _best_whole = ""      # whole match, for example : <data1, data2>
    _best_content = ""    # content, for example : data1, data2
    _found = False

    def __init__(self, input_string: str):
        self.detect_type(input_string)

    def detect_type(self, input: str):
        hit = re.search(r'<(.*)>', input)
        if hit and len(hit.group(0)) > self.len:
            self.assign_best(hit, DataType.XML_LIKE)

        hit = re.search(r'\((.+,.+)\)', input)
        if hit and len(hit.group(0)) > self.len:
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
        logger.warning("Anomaly, some data was right next to " \
        "the struct (without space), this data is thus lost : ", diff)

def list_replace(tagged_struct: list, tag: str, st: dict | list):
    for i in range(len(tagged_struct)):
        elem = tagged_struct[i]
        if type(elem) == str and tag in elem:
            check_anomaly(elem, tag)
            tagged_struct[i] = st

def dict_replace(tagged_struct: dict, tag: str, st: dict | list):
    for key in tagged_struct:
        elem = tagged_struct[key]
        if type(elem) == str and tag in elem:
            check_anomaly(elem, tag)
            tagged_struct[key] = st

def struct_replace(tagged_struct: dict | list, type: DataType, tag: str, st: dict | list):
    try:
        match type:
            case DataType.LIST:
                list_replace(tagged_struct, tag, st)

            case DataType.XML_LIKE:
                dict_replace(tagged_struct, tag, st)

            case _:
                pass
    
    except:
        logger.error("When rebuilding the struct in struct_replace, the argument 'type' doesn't correspond to the given tagged_struct")
        exit(1)

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
        # TODO check key uniqueness
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

def recursive_parse(input: str):
    input = input.strip()
    hit = Detect(input)
    tagged_content = hit.content
    tag_map = {}

    # recursion stop
    if not hit.found:
        return "", ""

    # recursion
    sub_string, sub_struct = recursive_parse(hit.content)

    if not sub_string:
        # form basic struct
        tagged_struct = parse_type(tagged_content, hit.type)
        return hit.whole_match, tagged_struct

    # replace struct by a unique tag
    tag = generate_tag()
    tagged_content = tagged_content.replace(sub_string, tag)

    # link tag with its computed struct
    tag_map[tag] = sub_struct

    # form basic struct
    tagged_struct = parse_type(tagged_content, hit.type)

    # include recursively computed struct
    struct_replace(tagged_struct, hit.type, tag, tag_map[tag])

    return hit.whole_match, tagged_struct

def parse(input_string: str):
    return recursive_parse(input_string)[1]


test_1 = '<class IORegistryEntry, id 0x100000100, retain 52>'
test_2 = '<class IORegistryEntry:IOService:IOPlatformExpertDevice, id 0x1000001cf, registered, matched, active, busy 0 (10227 ms), retain 29>'
test_3 = '<class IORegistryEntry:IOService:IODTNVRAM, id 0x10000010e, registered, matched, active, busy 0 (158 ms), retain 11>'
test_4 = '<class IORegistryEntry:IOService:IODTNVRAMDiags, id 0x1000001d0, registered, matched, active, busy 0 (33 ms), retain 6>'
test_5 = '<class IORegistryEntry, id (0x100000, 0x200000), retain 52>'
test_6 = '<class IORegistryEntry, id <0x100000, 0x200000>, user <alec, gilles>, retain 52>'
test_7 = '<key: value, id idval, mykey: (myval, myval2), otherkey (otherval, otherval2)>'

print(parse(test_7))
