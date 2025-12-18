from enum import Enum


class Type(Enum):
    NONE = 0
    STRING_SINGLE = 1
    STRING_DOUBLE = 2
    STRING_HOOK = 3
    XML_DICT = 4
    CURLY_DICT = 5
    MUTATED_STRING = 6
    LIST = 7


class String:
    type = Type.NONE
    start_char = "'", '"'
    end_char = "'", '"'

    def __init__(self):
        self.data = ""

    def handle_char(self, c):
        match c:
            case _:
                if isinstance(self.data, str):
                    self.data += c
                else:
                    print('ERROR : malformed data')
                    raise Exception

    def add_struct(self, struct):
        print("error not possible : set struct in string")

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


class StringDouble(String):
    type = Type.STRING_DOUBLE
    start_char = '"'
    end_char = '"'


class StringHook(String):
    type = Type.STRING_HOOK
    start_char = '['
    end_char = ']'


class StackBase(String):
    def add_struct(self, struct):
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
                    print("ERROR : chars found after a struct, should not happen")

    def values_reset(self):
        self.currently_key = True
        self.temp_key = ""
        self.temp_val = ""

    def end_chunk(self):
        if self.temp_key.strip():
            if isinstance(self.temp_val, str):
                self.temp_val = self.temp_val.strip()

            self.data[self.temp_key.strip()] = self.temp_val
            self.values_reset()

    def add_struct(self, struct):
        if self.currently_key:
            if isinstance(struct.data, str):
                self.temp_key += struct.data
            else:
                print("ERROR : non-string found as key to a dict. Using str(struct) instead")
                self.temp_key += str(struct.data)

        else:
            if isinstance(struct.data, str):
                self.temp_val += struct.data
            else:
                self.temp_val = struct.data

    def accepted_struct(self):
        if self.currently_key:
            return Type.STRING_SINGLE, Type.STRING_DOUBLE, Type.STRING_HOOK, Type.XML_DICT
        else:
            return Type

    def post_treatment(self):
        # case its not a dict but a string like <this_a_str>
        if list(self.data.values()) == [""]:
            self.data = "<" + next(iter(self.data)) + ">"
            self.type = Type.MUTATED_STRING


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
                    print("ERROR : found dangling characters after a struct in a list. Ignoring these character")

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
                print("ERROR : found dangling characters before a struct in a list. Ignoring these character : ")
                print(self.temp_data)
                print(struct.data)
                print()
                raise Exception

            self.temp_data = struct.data

    def accepted_struct(self):
        return Type

    def post_treatment(self):
        # case there is no comma, its a string , not a list. ex : (hello world)
        if len(self.data) == 1 and isinstance(self.data[0], str):
            self.data = "(" + self.data[0] + ")"
            self.type = Type.MUTATED_STRING


class Parser:
    def __init__(self):
        self.base_line = None
        self.stack = []

    def parse(self, str):
        self.base_line = str
        self.stack = [StackBase()]

        for c in self.base_line:
            self.base_switch(c)

        return self.stack[-1].data

    def base_switch(self, c):
        current_struct = self.stack[-1]
        possible = current_struct.accepted_struct()
        match c:

            case XmlDict.start_char if Type.XML_DICT in possible:
                self.stack.append(XmlDict())

            case XmlDict.end_char if current_struct.type is Type.XML_DICT:
                self.end_struct()

            case CurlyDict.start_char if Type.CURLY_DICT in possible:
                self.stack.append(CurlyDict())

            case CurlyDict.end_char if current_struct.type is Type.CURLY_DICT:
                self.end_struct()

            case StringSingle.start_char if Type.STRING_SINGLE in possible:
                self.stack.append(StringSingle())

            case StringSingle.end_char if current_struct.type is Type.STRING_SINGLE:
                self.end_struct()

            case StringDouble.start_char if Type.STRING_DOUBLE in possible:
                self.stack.append(StringDouble())

            case StringDouble.end_char if current_struct.type is Type.STRING_DOUBLE:
                self.end_struct()

            case StringHook.start_char if Type.STRING_HOOK in possible:
                self.stack.append(StringHook())

            case StringHook.end_char if current_struct.type is Type.STRING_HOOK:
                self.end_struct()

            case List.start_char if Type.LIST in possible:
                self.stack.append(List())

            case List.end_char if current_struct.type is Type.LIST:
                self.end_struct()

            case _:
                self.stack[-1].handle_char(c)

    def current_type_is(self, type):
        return self.stack[-1].type == type

    def end_struct(self):
        try:
            struct = self.stack.pop()
            struct.end_chunk()
            struct.post_treatment()
            self.stack[-1].add_struct(struct)

        except Exception:
            # print(self.base_line)
            pass
