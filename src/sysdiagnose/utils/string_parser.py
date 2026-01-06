from enum import Enum
from sysdiagnose.utils.base import logger


class Type(Enum):
    NONE = 0
    STRING_SINGLE = 1
    STRING_DOUBLE = 2
    XML_DICT = 3
    CURLY_DICT = 4
    MUTATED_STRING = 5
    LIST = 6
    HOOK_LIST = 7


"""
The structure classes all follow the same format with these mandatory methods and attributes :

    Attributes
        type       : The type of the struct (Type enum)
        start_char : The character that opens the structure
        end_char   : The character that closes the structure

    Methods
        handle_char(c)     : handles the characters found inside the structure
        add_struct(struct) : embeds another struct inside the current struct
        accepted_struct()  : returns a list of structs that can be embed (ex: a dict cannot be embed in a string)
        end_chunk()        : end of a section in the struct, for ex. each list separator ',' calls this
        post_treatment()   : treatment at the very end of the structure.
                             some structs can change form at the end, for ex. '<hello world>'
                             will be changed from XML_DICT to a string (MUTATED_STRING)
"""
class String:
    type = Type.NONE
    start_char = "'", '"'
    end_char = "'", '"'

    def __init__(self):
        self.data = ""

    def handle_char(self, c):
        if isinstance(self.data, str):
            self.data += c
        else:
            logger.error('ERROR : malformed data, random character found next to a structure')
            raise ValueError('malformed data, random character found next to a structure')

    def add_struct(self, struct):
        logger.error("ERROR : This function should never be called, if you see this there is a coding mistake")
        raise Exception("Code that shouldn't be called was called")

    def accepted_struct(self):
        return Type.NONE,

    def end_chunk(self):
        pass

    def post_treatment(self):
        self.data = self.start_char + self.data + self.end_char


class StringSingle(String):
    type = Type.STRING_SINGLE
    start_char = "'"
    end_char = "'"

    def post_treatment(self):
        pass


class StringDouble(String):
    type = Type.STRING_DOUBLE
    start_char = '"'
    end_char = '"'

    def post_treatment(self):
        pass


class StackBase(String):
    def add_struct(self, struct):
        if struct.data:
            self.data = struct.data
            self.type = struct.type

    def accepted_struct(self):
        return Type


class XmlDict:
    type = Type.XML_DICT
    start_char = "<"
    end_char = ">"
    separator = " "

    def __init__(self):
        self.data = {}
        self.currently_key = True
        self.temp_key = ""
        self.temp_val = ""

        # fixes a special case '<"!!J>">' where we dont want the ! interpreted as a bool
        self.flag_key_is_string = False

    def handle_char(self, c):
        match c:
            case self.separator if self.currently_key:
                if self.temp_key:
                    self.currently_key = False

            case ",":
                self.end_chunk()

            case _:
                if self.currently_key:
                    self.temp_key += c
                elif isinstance(self.temp_val, str):
                    self.temp_val += c
                elif c != " ":
                    logger.error("ERROR : Chars found AFTER a struct")

    def values_reset(self):
        self.currently_key = True
        self.temp_key = ""
        self.temp_val = ""
        self.flag_key_is_string = False

    def end_chunk(self):
        if self.temp_key.strip():
            self.temp_key = self.temp_key.strip()
            if isinstance(self.temp_val, str):
                self.temp_val = self.temp_val.strip()

            # special case, key without val -> true/false value
            if not self.temp_val and self.currently_key and not self.flag_key_is_string:
                if self.temp_key[0] == '!':
                    self.temp_key = self.temp_key[1:]
                    self.temp_val = False
                else:
                    self.temp_val = True

            # case the value is a number, make it a number
            if isinstance(self.temp_val, str) and self.temp_val.isdigit():
                self.temp_val = int(self.temp_val)

            self.data[self.temp_key] = self.temp_val
            self.values_reset()

    def add_struct(self, struct):
        if self.currently_key:
            if isinstance(struct.data, str):
                self.temp_key += struct.data
                self.flag_key_is_string = True
            else:
                logger.error("ERROR : Non-string found as key to a dict. Using str(struct) instead")
                self.temp_key += str(struct.data)

        else:
            if isinstance(struct.data, str):
                self.temp_val += struct.data
            else:
                self.temp_val = struct.data

    def accepted_struct(self):
        if self.currently_key:
            return Type.STRING_SINGLE, Type.STRING_DOUBLE, Type.XML_DICT, Type.CURLY_DICT, Type.LIST, Type.HOOK_LIST
        else:
            return Type

    def post_treatment(self):
        # case its not a dict but a string like <this_a_str>
        if list(self.data.values()) in ([""], [True], [False]):
            self.data = "<" + next(iter(self.data)) + ">"
            self.type = Type.MUTATED_STRING

        # case it has multiple keys, without values its a list
        elif self.data and all(v == "" for v in self.data.values()):
            self.data = list(self.data.keys())
            self.type = Type.LIST   # might be unacurate since its a mutated list but shouldn't matter


class CurlyDict(XmlDict):
    type = Type.CURLY_DICT
    start_char = "{"
    end_char = "}"
    separator = "="


class List:
    type = Type.LIST
    start_char = "("
    end_char = ")"

    def __init__(self):
        self.data = []
        self.temp_data = ""

    def handle_char(self, c):
        match c:
            case ",":
                self.end_chunk()

            case _:
                if isinstance(self.temp_data, str):
                    self.temp_data += c
                elif c != " ":
                    logger.error("ERROR : Found random characters AFTER a struct in a list. Ignoring these character")

    def end_chunk(self):
        if isinstance(self.temp_data, str):
            self.data.append(self.temp_data.strip())

        else:
            self.data.append(self.temp_data)

        self.temp_data = ""

    def add_struct(self, struct):
        if isinstance(struct.data, str):
            self.temp_data += struct.data

        else:
            if self.temp_data.strip():
                print("ERROR : Found random characters BEFORE a struct in a list. Ignoring these character")

            self.temp_data = struct.data

    def accepted_struct(self):
        return Type

    def post_treatment(self):
        # case there is no comma, its a string , not a list. ex : (hello world)
        if len(self.data) == 1 and isinstance(self.data[0], str):
            self.data = self.start_char + self.data[0] + self.end_char
            self.type = Type.MUTATED_STRING

        # case we have useless (), ex : '((a, b))' same as '(a, b)' or even '(({a: b}))' same as '{a: b}'
        elif len(self.data) == 1:
            self.data = self.data[0]
            self.type = Type.NONE


class HookList(List):
    type = Type.HOOK_LIST
    start_char = "["
    end_char = "]"


class Parser:
    def __init__(self):
        self.base_line = None
        self.stack = []

    def parse(self, line):
        self.base_line = line
        self.stack = [StackBase()]

        for c in self.base_line:
            self.base_switch(c)

        return self.treat_final_value()

    def base_switch(self, c):
        current_struct = self.stack[-1]
        possible = current_struct.accepted_struct()     # list of types that the current struct can accept
        match c:

            # XML Dict : <k1 v1, k2 v2>
            case XmlDict.start_char if Type.XML_DICT in possible:
                self.stack.append(XmlDict())

            case XmlDict.end_char if current_struct.type is Type.XML_DICT:
                self.end_struct()

            # Curly Dict : {k1=v1, k2=v2}
            case CurlyDict.start_char if Type.CURLY_DICT in possible:
                self.stack.append(CurlyDict())

            case CurlyDict.end_char if current_struct.type is Type.CURLY_DICT:
                self.end_struct()

            # String Single quote : 'hello world'
            case StringSingle.start_char if Type.STRING_SINGLE in possible:
                self.stack.append(StringSingle())

            case StringSingle.end_char if current_struct.type is Type.STRING_SINGLE:
                self.end_struct()

            # String Double quotes : "hello world"
            case StringDouble.start_char if Type.STRING_DOUBLE in possible:
                self.stack.append(StringDouble())

            case StringDouble.end_char if current_struct.type is Type.STRING_DOUBLE:
                self.end_struct()

            # Hook List : [v1, v2, v3]
            case HookList.start_char if Type.HOOK_LIST in possible:
                self.stack.append(HookList())

            case HookList.end_char if current_struct.type is Type.HOOK_LIST:
                self.end_struct()

            # Bracket List : (v1, v2, v3)
            case List.start_char if Type.LIST in possible:
                self.stack.append(List())

            case List.end_char if current_struct.type is Type.LIST:
                self.end_struct()

            # Default just handle the char inside the current struct
            case _:
                self.stack[-1].handle_char(c)

    def end_struct(self):
        struct = self.stack.pop()
        struct.end_chunk()
        struct.post_treatment()
        self.stack[-1].add_struct(struct)

    def treat_final_value(self):
        # case the value is a number, make it a number
        finaldata = self.stack[-1].data
        if isinstance(finaldata, str) and finaldata.isdigit():
            finaldata = int(finaldata)
        return finaldata
