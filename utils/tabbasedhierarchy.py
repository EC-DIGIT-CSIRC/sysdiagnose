import re


def parse_tab_based_hierarchal_file(path: str) -> list | dict:
    with open(path, 'r') as f:
        lines = f.readlines()
        result = parse_block(lines)
    return result


def parse_block(lines: list) -> list | dict:
    result = None
    n = 0
    while n < len(lines):
        line = lines[n]
        if line.strip() == '}' or line.strip() == '':
            n = n + 1
            continue
        # subsection if next line is more indented  (more tabs at start of line)
        current_depth = len(line) - len(line.lstrip('\t'))
        try:
            next_depth = len(lines[n + 1]) - len(lines[n + 1].lstrip('\t'))
        except IndexError:  # catch for handling last line
            next_depth = current_depth
        if next_depth > current_depth:
            # subsection
            # extract key
            key = line.replace(':', '').replace('{', '').strip()
            # identify end of subsection and call recursive parsing function with that block
            extracted_block = []
            while next_depth > current_depth:
                n = n + 1
                extracted_block.append(lines[n])
                try:
                    next_depth = len(lines[n + 1]) - len(lines[n + 1].lstrip('\t'))
                except IndexError:
                    next_depth = current_depth
            # store the result
            if not result:
                result = {}
            result[key] = parse_block(extracted_block)
            # n is already at the right offset
            n = n + 1
            pass
        else:
            # extract key, val using regex
            regexes = [
                r'^(.+?)=>*(.+)',   # key_without_spaces => value
                r'^([^:]+):(.*)'    # key_with_spaces: value
            ]
            key = None
            value = None
            for regex in regexes:
                match = re.match(regex, line.strip())
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    break
            if key:
                if not result:
                    result = {}
                result[key.strip()] = value.strip()
            else:
                if not result:
                    result = []
                result.append(line.strip())

            n = n + 1  # skip to next line
    return result
