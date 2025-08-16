from tests import SysdiagnoseTestCase
from sysdiagnose.utils.base import Event
import unittest
import orjson
import orjsonl
import timeit
import json
from pathlib import Path


class TestOrjson(SysdiagnoseTestCase):

    def test_orjson(self):
        for case in self.sd.cases():
            fname = Path(self.sd.config.get_case_parsed_data_folder(case_id=case)) / 'logarchive.jsonl'

            print(f"Benchmarking {fname}...")
            # print("load_orjsonl_dict: ", end=" ")
            # print(timeit.timeit(lambda: self.load_orjsonl_dict(fname)", number=3))
            # print("load_orjsonl_dataclass: ", end=" ")
            # print(timeit.timeit(lambda: self.load_orjsonl_dataclass(fname)", number=3))
            print("load_save_dumps_orjson_dict: ", end=" ")
            print(timeit.timeit(lambda: self.load_save_dumps_orjson_dict(fname), number=3))
            print("load_save_dumpstodict_orjson_dict: ", end=" ")
            print(timeit.timeit(lambda: self.load_save_dumpstodict_orjson_dict(fname), number=3))
            # Uncomment the following lines if you want to test without datetime

            # print("load_orjsonl_dataclass_nodatetime: ", end=" ")
            # print(timeit.timeit(lambda: self.load_orjsonl_dataclass_nodatetime(fname)", number=3))
            # print("load_orjson_dict: ", end=" ")
            # print(timeit.timeit(lambda: self.load_orjson_dict(fname)", number=3))
            # print("load_plist_dict: ", end=" ")
            # print(timeit.timeit(lambda: self.load_plist_dict(fname)", number=3))
            # print("load_plist_dataclass: ", end=" ")
            # print(timeit.timeit(lambda: self.load_plist_dataclass(fname)", number=3))

    def load_orjsonl_dict(self, fname: Path):
        data = orjsonl.stream(fname)
        i = 0
        for item in data:
            # self.assertIsInstance(item, dict)
            i += 1

        # print(f'Loaded {i} items')
        self.assertGreater(i, 0)

    def load_orjsonl_dataclass(self, fname: Path):
        data = orjsonl.stream(fname)
        i = 0
        for item in data:
            e = Event.from_dict(item)
            # self.assertIsInstance(e, Event)
            i += 1

        # print(f'Loaded {i} items')
        self.assertGreater(i, 0)

    # def load_orjsonl_dataclass_nodatetime(self, fname: Path):
    #     data = orjsonl.stream(fname)
    #     i = 0
    #     for item in data:
    #         e = EventNoDatetime.from_dict(item)
    #         #self.assertIsInstance(e, EventNoDatetime)
    #         i += 1

    #     # print(f'Loaded {i} items')
    #     self.assertGreater(i, 0)

    def load_orjson_dict(self, fname: Path):
        i = 0
        with open(fname, 'r', encoding='utf-8') as f:
            for line in f:
                item = orjson.loads(line)
                # self.assertIsInstance(item, dict)
                i += 1

        # print(f'Loaded {i} items')
        self.assertGreater(i, 0)

    def load_save_dumps_orjson_dict(self, fname: Path):
        i = 0
        with open(fname, 'r', encoding='utf-8') as f_in:
            with open('/tmp/logarchive.jsonl', 'wb') as f_out:
                for line in f_in:
                    item = orjson.loads(line)
                    e = Event.from_dict(item)
                    f_out.write(orjson.dumps(e))
                    i += 1

    def load_save_dumpstodict_orjson_dict(self, fname: Path):
        i = 0
        with open(fname, 'r', encoding='utf-8') as f_in:
            with open('/tmp/logarchive.jsonl', 'wb') as f_out:
                for line in f_in:
                    item = orjson.loads(line)
                    e = Event.from_dict(item)
                    f_out.write(orjson.dumps(e.to_dict()))
                    i += 1

    # def load_plist_dict(self, fname: Path):
    #     i = 0
    #     with open(fname, 'r', encoding='utf-8') as f:
    #         for line in f:
    #             item = json.loads(line)
    #             #self.assertIsInstance(item, dict)
    #             i += 1

    #     # print(f'Loaded {i} items')
    #     self.assertGreater(i, 0)

    # def load_plist_dataclass(self, fname: Path):
    #     i = 0
    #     with open(fname, 'r', encoding='utf-8') as f:
    #         for line in f:
    #             item = Event.from_dict(json.loads(line))
    #             #self.assertIsInstance(item, Event)
    #             i += 1

    #     # print(f'Loaded {i} items')
    #     self.assertGreater(i, 0)

    # def load_plist_dataclass_nodatetime(self, fname: Path):
    #     i = 0
    #     with open(fname, 'r', encoding='utf-8') as f:
    #         for line in f:
    #             item = EventNoDatetime.from_dict(json.loads(line))
    #             #self.assertIsInstance(item, EventNoDatetime)
    #             i += 1

    #     # print(f'Loaded {i} items')
    #     self.assertGreater(i, 0)


if __name__ == '__main__':
    unittest.main()
