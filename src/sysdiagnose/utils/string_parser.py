import re
from enum import Enum
from sysdiagnose.utils.base import logger
import uuid


class DataType(Enum):
    XML_DICT = 1
    CURLY_DICT = 2
    LIST = 3
    STRING = 4
    UNKNOWN = 5

class Detect:
    _best_len = float('inf')
    _best_type = DataType.UNKNOWN
    _best_whole = ""      # whole match, for example : <data1, data2>
    _best_content = ""    # content, for example : data1, data2
    _found = False

    def __init__(self, input_string: str):
        self.detect_type(input_string)

    def detect_type(self, input: str):
        """         Note on the match types

            XML_DICT : data inside <> with at least a comma or space between chars
                excluded : <> , < > , <       >

            CURLY_DICT : like xml_dict but with {} instead of <>

            LIST : data in parentheses ('[]', '()') or d-quotes with at least one comma
                   Note : most of basic d-quotes have been sinitized in prepare_data()

            STRING : parentheses that dont contain any comma.
                example : I'm good at coding (not really)  <-- shouldn't be a list, simply text

        """  # noqa: W605

        # find simple double-quotes ex : "hello world"
        hit = re.search(r'"([^"]*)"', input)
        if hit and len(hit.group(0)) < self._best_len:
            self.assign_best(hit, DataType.STRING)

        # find xml like dict ex : <key value, k2 v2>
        hit = self.find_smallest(r'<([^<>]*([,]|[^\s<>][\s]+[^\s<>])[^<>]*)>', input)
        if hit and len(hit.group(0)) < self._best_len:
            self.assign_best(hit, DataType.XML_DICT)

        # find dict in {} ex : {key1=val1, k2=v2}
        hit = self.find_smallest(r'{([^{}]*)}', input)
        if hit and len(hit.group(0)) < self._best_len:
            self.assign_best(hit, DataType.CURLY_DICT)

        # find list in parentheses ex : (a, b, c)
        hit = self.find_smallest(r'\(([^()]*,[^()]*)\)', input)
        if hit and len(hit.group(0)) < self._best_len:
            self.assign_best(hit, DataType.LIST)

        # find simple string data in <> ex : <648a4c>
        hit = re.search(r'(<[^,<>\s]*>)', input)
        if hit and len(hit.group(0)) < self._best_len:
            self.assign_best(hit, DataType.STRING)

        # find simple parentheses without ',' ex : (hello world)
        hit = re.search(r'(\([^,)(]*\))', input)
        if hit and len(hit.group(0)) < self._best_len:
            self.assign_best(hit, DataType.STRING)

        # find [] parentheses without ',' nor '=' ex : [hello world]
        hit = re.search(r'(\[[^,=\[\]]*\])', input)
        if hit and len(hit.group(0)) < self._best_len:
            self.assign_best(hit, DataType.STRING)

    def assign_best(self, hit: re.Match, type: DataType):
        self._best_len = len(hit.group(0))
        self._best_type = type
        self._best_whole = hit.group(0)
        self._best_content = hit.group(1)
        self._found = True

    def find_smallest(self, regex: str, data: str) -> re.Match:
        pattern = re.compile(regex)
        matches = list(pattern.finditer(data))
        if not matches:
            return None
        return min(matches, key=lambda m: len(m.group(0)))

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
    structured = s.replace(tag, '[STRUCT]')
    # cases we dont have to warn about. ex : ((<key: val>)) is same as <key: val>

    if tag in s and diff and not is_redundent_syntax_regex(diff):
        logger.warning("Warning : Anomaly: some data was right next to "
                       "the struct (without space), this data is thus lost\n---> " + structured)

def is_redundent_syntax_regex(s: str) -> re.Match:
    """ If we have for example ([ ]) around a struct, we consider it useless
        Example : "[(<key value, k1 v1>)]" is the same as <key value, k1 v1> """
    return re.search(r'^[(){}\[\]<>""]+$', s)

def prepare_line(line: str) -> str:
    """ remove unnecessary double-quotes
    quotes are needed when a comma is inside.
        example :
        <key1 val1, k2 "hello, world"> != <key1 val1, k2 hello, world>

    Note : regex cant be used, need to be statefull i.e. consider opening and closing quotes
        example that doesnt work with regex: "a,"b"c,"
        gives : '"a,bc,"'
        should give : '"a,"b"c,"'
        (the quotes in "a," aren't removed bcs of the comma, so "b" is detected as a string)
    """
    inside = False
    opening_pos = None
    skipping = False
    parse_char = (',', '=', '{', '}', '(', ')', '<', '>')
    line = line.strip()

    i = 0
    while i < len(line):
        if line[i] == '"':
            if inside:
                if not skipping:
                    line = line[:i] + line[i + 1:]    # remove last "
                    line = line[:opening_pos] + line[opening_pos + 1:]    # remove first "
                    i -= 1
                else:
                    i += 1
                inside = False

            else:
                inside = True
                opening_pos = i
                skipping = False
                i += 1
            continue

        if inside and line[i] in parse_char:
            skipping = True

        i += 1

    return line

def check_key_uniqueness(dictio: dict, key: str):
    if dictio.get(key):
        logger.warning('Warning : Key is already in dictionary, data may be lost\n---> ' + key)


def parse_list(input_string: str) -> list:
    list_of_elements = input_string.split(',')
    res = []

    for element in list_of_elements:
        res.append(element.strip())

    return res


def parse_dict(input_string: str, separator: str) -> dict:
    list_of_elements = input_string.split(',')
    res = {}

    if list_of_elements == ['']:
        return res

    for element in list_of_elements:
        element = element.strip()
        splitted = element.split(separator, 1)
        key = splitted[0]

        # value is true/false if there is only a key
        if len(splitted) > 1:
            value = splitted[1].strip()
        elif key[0] == '!':
            value = 'false'
            key = key[1:]
        else:
            value = 'true'

        check_key_uniqueness(res, key)
        res[key] = value

    return res


def parse_type(input_string: str, type: DataType) -> dict | list | str:
    match type:
        case DataType.XML_DICT:
            return parse_dict(input_string, ' ')

        case DataType.CURLY_DICT:
            return parse_dict(input_string, '=')

        case DataType.LIST:
            return parse_list(input_string)

        case DataType.STRING:
            return input_string

        case _:
            logger.error("Error : Type not found in parse_type(). (Note : "
                         "you probably forgot to add it to the match case)")

def resolve_tag_list_dict(final_struct: list | dict, elem: list | dict | str, key: str, tag: str, constructed: dict | list | str) -> bool:
    if isinstance(elem, str) and tag in elem:
        if isinstance(constructed, str):
            final_struct[key] = final_struct[key].replace(tag, constructed)
        else:
            check_anomaly(elem, tag)
            final_struct[key] = constructed
        return True

    elif isinstance(key, str) and tag in key:   # only for dict, key is int for list
        if isinstance(constructed, str):
            new_key = key.replace(tag, constructed)
            value = final_struct[key]
            del final_struct[key]
            final_struct[new_key] = value
        else:
            logger.error("Error : Trying to use a struct as a key in a dict")
            final_struct[key] = constructed
        return True

    elif isinstance(elem, list):
        if resolve_tag_list(elem, tag, constructed):
            return True

    elif isinstance(elem, dict):
        if resolve_tag_dict(elem, tag, constructed):
            return True

    return False

def resolve_tag_dict(final_struct: dict, tag: str, constructed: dict | list | str) -> bool:
    for key in final_struct:
        elem = final_struct[key]
        if resolve_tag_list_dict(final_struct, elem, key, tag, constructed):
            return True

    return False

def resolve_tag_list(final_struct: list, tag: str, constructed: dict | list | str):
    for i in range(len(final_struct)):
        elem = final_struct[i]
        if resolve_tag_list_dict(final_struct, elem, i, tag, constructed):
            return True

    return False

def resolve_tag_str(final_struct: dict | list | str, tag: str, constructed: dict | list | str) -> dict | list | str:
    if not isinstance(constructed, str):
        if final_struct.replace(tag, "") == '()':
            final_struct = constructed
        else:
            user_friendly = final_struct.replace(tag, "[STRUCT]")
            lost_data = final_struct.replace(tag, "")
            if not is_redundent_syntax_regex(lost_data) and lost_data:
                logger.warning("Warning : trying to incorporate dict/list in a string :\n---> " + user_friendly)
            final_struct = constructed
    else:
        final_struct = final_struct.replace(tag, constructed)

    return final_struct

def resolve_tag(final_struct: dict | list | str, tag: str, constructed: dict | list | str) -> dict | list | str:
    if isinstance(final_struct, dict):
        resolve_tag_dict(final_struct, tag, constructed)

    elif isinstance(final_struct, list):
        resolve_tag_list(final_struct, tag, constructed)

    elif isinstance(final_struct, str):
        final_struct = resolve_tag_str(final_struct, tag, constructed)

    else:
        logger.error('Error : struct type not found : ' + str(type(final_struct)))
        raise ValueError("Structure passed has to be a dict, a list or a string. Type : " + str(type(final_struct)))

    # return is necessary, strings are not passed by reference in python
    return final_struct

def parse_main_loop(data_string: str) -> dict | list | str:

    # Detection
    hit = Detect(data_string)
    final_struct = None
    tag_stack = []
    constructed_stack = []

    # ----------- parse string -----------
    while hit.found:
        # form basic struct
        constructed = parse_type(hit.content, hit.type)

        # replace struct by an unique tag
        tag = generate_tag()
        data_string = data_string.replace(hit.whole_match, tag, 1)

        # add tag and constructed to stack, to rebuild later
        tag_stack.append(tag)
        constructed_stack.append(constructed)

        hit = Detect(data_string)

    # ----------- reconstruct -----------
    while tag_stack:
        tag = tag_stack.pop()
        constructed = constructed_stack.pop()

        final_struct = resolve_tag(final_struct or tag, tag, constructed)

    return final_struct

def parse(data_string: str) -> dict | list | str:

    # greatly optimizes the process
    data_string = prepare_line(data_string)

    data_string = parse_main_loop(data_string) or data_string

    return data_string
