from sysdiagnose.utils.base import logger
from sysdiagnose.utils.ioreg_parsers.string_parser import IORegStringParser
import re

class IORegStructParser:
    rollback_addr = None
    line = None

    def __init__(self):
        pass

    def get_dict(self, file_path):
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
            logger.warning('Key is already in dictionary, data may be lost')

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
        self.dict_update(data_tree, data_dict)

        return res

    def dict_update(self, main_dict, data_dict):
        data_dict_len = len(data_dict)
        main_dict_len = len(main_dict)
        main_dict.update(data_dict)

        if len(main_dict) != data_dict_len + main_dict_len:
            logger.warning("One of the keys was already present in the json, data loss may occur")

    def parse_title(self):
        if "+-o" not in self.line:
            logger.warning("'non-title' line given to title parser, should not happen")
            return ""

        whole_title = self.line.split("+-o", 1)[1].strip()

        if "<class" not in whole_title or whole_title[-1] != '>':
            logger.warning("Title doesnt respect the usual <class ... > format, to invesstigate")

        name = whole_title.split('<class', 1)[0].strip()
        data = "".join(whole_title.split('<class', 1)[1:])[:-1].strip()

        return name, data

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
                self.check_key_uniqueness(data_tree, name)
                data_tree[name] = {}
                self.recursive_call(data_tree[name])

            else:
                self.get_line()

    def recursive_fun(self, data_tree: dict):
        is_leaf = False
        self.get_line()

        # check if we're at the start of a node
        self.check_start_node()

        additional_data = self.parse_title()[1]
        additional_data = IORegStringParser().get_parsed(additional_data)
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
