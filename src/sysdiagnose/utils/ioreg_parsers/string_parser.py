import re
from enum import Enum
from sysdiagnose.utils.base import logger
import uuid

class DataType(Enum):
    XML_LIKE = 1
    LIST = 2
    STRING = 3
    UNKNOWN = 4

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

            XML_LIKE : data inside < >

            LIST : data in parentheses with at least one comma

            STRING : parentheses that dont contain any comma.
                example : I'm good at coding (not really)  <-- shouldn't be a list, simply text

        """  # noqa: W605

        # find xml like dict ex : <key value, k2 v2>
        hit = re.search(r'<([^<>]*)>', input)
        if hit and len(hit.group(0)) < self._best_len:
            self.assign_best(hit, DataType.XML_LIKE)

        # find list in parentheses ex : (a, b, c)
        hit = re.search(r'\(([^()]*,[^()]*)\)', input)
        if hit and len(hit.group(0)) < self._best_len:
            self.assign_best(hit, DataType.LIST)

        # find simple parentheses without ',' ex : (hello world)
        hit = re.search(r'(\([^,)(]*\))', input)
        if hit and len(hit.group(0)) < self._best_len:
            self.assign_best(hit, DataType.STRING)

        self.warn_unknown_struct(input)

    def assign_best(self, hit: re.Match, type: DataType):
        self._best_len = len(hit.group(0))
        self._best_type = type
        self._best_whole = hit.group(0)
        self._best_content = hit.group(1)
        self._found = True

    def warn_unknown_struct(self, input: str):
        main_cond = self._best_type is DataType.UNKNOWN
        cond_1 = '<' in input and '>' in input
        cond_2 = '(' in input and ')' in input
        cond_3 = '[' in input and ']' in input
        cond_4 = '{' in input and '}' in input

        if (main_cond and (cond_1 or cond_2 or cond_3 or cond_4)):
            logger.warning('Warning : A structure might have been recognized '
                           'in here, if so please consider adding it to the '
                           'string_parser.py file\n---> ' + input)

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
        value = element.split(' ', 1)[1].strip()
        # TODO if only a key is present, add true as value
        check_key_uniqueness(res, key)
        res[key] = value

    return res


def parse_type(input_string: str, type: DataType):
    match type:
        case DataType.XML_LIKE:
            return parse_xml_like(input_string)

        case DataType.LIST:
            return parse_list(input_string)

        case DataType.STRING:
            return input_string

        case _:
            logger.error("Error : Type not found in parse_type(). (Note : "
                         "you probably forgot to add it to the match case)")


def resolve_tag_dict(final_struct: dict, tag: str, constructed: dict | list):
    for key in final_struct:
        elem = final_struct[key]

        if isinstance(elem, str) and tag in elem:
            if isinstance(constructed, str):
                final_struct[key] = final_struct[key].replace(tag, constructed)
            else:
                check_anomaly(elem, tag)
                final_struct[key] = constructed
            return True

        elif isinstance(elem, list):
            if resolve_tag_list(elem, tag, constructed):
                return True

        elif isinstance(elem, dict):
            if resolve_tag_dict(elem, tag, constructed):
                return True

    return False


def resolve_tag_list(final_struct: list, tag: str, constructed: dict | list):
    for i in range(len(final_struct)):
        elem = final_struct[i]

        # TODO repetition with resolve_tag_dict, put in a func
        if isinstance(elem, str) and tag in elem:
            if isinstance(constructed, str):
                final_struct[i] = final_struct[i].replace(tag, constructed)
            else:
                check_anomaly(elem, tag)
                final_struct[i] = constructed
            return True

        elif isinstance(elem, list):
            if resolve_tag_list(elem, tag, constructed):
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
    data_string = data_string.replace(hit.whole_match, tag, 1)

    # recursion
    final_struct = parse(data_string)

    # reconstruct data structure
    if not final_struct:
        final_struct = constructed      # at the root
    else:
        resolve_tag(final_struct, tag, constructed)

    return final_struct
