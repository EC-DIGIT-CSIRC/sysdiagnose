from sysdiagnose.utils.base import logger
from sysdiagnose.utils.ioreg_parsers import string_parser
import re

class IORegStructParser:
    rollback_addr = None
    line = None

    def __init__(self):
        pass

    def parse(self, file_path):
        data_tree = {}

        with open(file_path, 'r', errors='backslashreplace') as f:
            self.open_file = f
            self.recursive_fun(data_tree)

        return data_tree

    def get_line(self):
        self.rollback_addr = self.open_file.tell()
        self.line = self.open_file.readline()
        self.line = self.line.replace('\n', '')

    def recursive_call(self, data_tree: dict):
        self.open_file.seek(self.rollback_addr)
        self.recursive_fun(data_tree)

    def check_start_node(self):
        if '+-o' not in self.line:
            logger.error('This is not normal. Recursive function called on random line.')
            exit(1)

    def not_empty_node_check(self):
        if not self.rollback_addr:
            logger.error("+-o in two consecutive lines, not supposed to be possible")
            exit(1)

    def check_key_uniqueness(self, dictio: dict, key: str):
        if dictio.get(key):
            logger.warning('Key is already in dictionary, data may be lost\n\tKey : ' + key)

    def fetch_node_data(self, data_tree: dict) -> bool:
        node_data = []  # array of lines, to be transformed in json
        res = True

        while '+-o' not in self.line:
            if not self.line:   # end of file
                res = False
                break

            node_data.append(self.line)
            self.get_line()

        data_dict = self.node_data_to_json(node_data)
        self.parse_values(data_dict)
        self.dict_update(data_tree, data_dict)

        return res

    def parse_values(self, data_dict: dict):
        for key in data_dict:
            value = data_dict[key]
            constructed = string_parser.parse(value)
            if constructed:
                data_dict[key] = constructed

    def dict_update(self, main_dict: dict, data_dict: dict):
        """ Redefining the dict.update function to handle key collisions """

        for key in data_dict:
            if main_dict.get(key):
                if isinstance(main_dict[key], list):
                    main_dict[key].append(data_dict[key])
                else:
                    main_dict[key] = [main_dict[key], data_dict[key]]
            else:
                main_dict[key] = data_dict[key]

    def parse_title(self) -> tuple:
        if "+-o" not in self.line:
            logger.warning("'non-title' line given to title parser, should not happen")
            return "", ""

        whole_title = self.line.split("+-o", 1)[1].strip()

        if "<class" not in whole_title or whole_title[-1] != '>':
            logger.warning("Title doesnt respect the usual <class ... > format, to invesstigate")

        name = whole_title.split('<class', 1)[0].strip()
        data = '<class ' + "".join(whole_title.split('<class', 1)[1:]).strip()

        return name, data

    def warn_if_no_struct(self, data: str | dict | list):
        if isinstance(data, str):
            logger.warning("No struct found in a title, should always have one\n---> " + data)

    def handle_anomalies(self, dictio: dict, data: str, key: str) -> bool:
        """
            some values overflow on the few next lines
            this condition assumes there is no '=' in the exceeding data
            (which was the case up to what I saw)

            p.s. :  if you wonder why cond4 is necessary, it is only for
                    the last leaf, which has no '|' symbols. without cond4,
                    these lines would be seen as anomalies
        """
        cond1 = not re.search(r'^\s*\|+', data)
        cond2 = len(data.strip()) > 0
        cond3 = data.strip() not in ('{', '}')
        cond4 = '=' not in data

        if cond1 and cond2 and cond3 and cond4:
            dictio[key] += data.strip()
            return True
        return False

    def node_data_to_json(self, data_array: list[str]) -> dict:
        res = {}
        key = None

        for data in data_array:
            self.handle_anomalies(res, data, key)

            # remove spaces and pipes at start
            clean_line = re.sub(r'^(\s|\|)*', '', data)

            if '=' not in clean_line:
                continue

            # split at the first equal only
            key, value = clean_line.split('=', 1)

            # remove first and last " (in case the key has more quotes inside)
            key = key.replace('"', '', 1)
            key = key[::-1].replace('"', '', 1)[::-1]
            key = key.strip()

            self.check_key_uniqueness(res, key)
            res[key] = value.strip()

        return res

    def iterate_children(self, depth: int, data_tree: dict):
        while self.line and (self.line[depth] == '|' or self.line[depth: depth + 3] == '+-o'):
            if self.line[depth: depth + 3] == '+-o':
                name = self.parse_title()[0]
                new_child = self.setup_new_child(data_tree, name)
                self.recursive_call(new_child)

            else:
                self.get_line()

    def setup_new_child(self, data_tree: dict, key: str) -> dict:
        """ This function is dedicated to iterate_children, it handles the special cases
            where a node name is already present for the same parent """

        if data_tree.get(key):
            if isinstance(data_tree[key], list):
                # case already list of data nodes
                data_tree[key].append({})
            else:
                # case currently single data node
                data_tree[key] = [data_tree[key], {}]
            return data_tree[key][-1]

        else:
            # case new key
            data_tree[key] = {}
            return data_tree[key]

    def recursive_fun(self, data_tree: dict):
        is_leaf = False
        self.get_line()

        # check if we're at the start of a node
        self.check_start_node()

        # try to get a struct out of the data
        title_data = self.parse_title()[1]
        additional_data = string_parser.parse(title_data) or title_data
        self.warn_if_no_struct(additional_data)

        self.dict_update(data_tree, additional_data)

        depth = self.line.index('o')  # to identify the other nodes that have the same parent
        self.get_line()

        # check if its a leaf
        if self.line[depth] != '|':
            is_leaf = True

        # Fetch the data of the node
        if not self.fetch_node_data(data_tree):
            return  # EOF

        # stop if we're a leaf
        if is_leaf:
            self.open_file.seek(self.rollback_addr)
            return

        # sanity check
        self.not_empty_node_check()

        # Iterates over each child to call the current function
        self.iterate_children(depth, data_tree)
