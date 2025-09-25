from sysdiagnose.utils.ioreg_parsers.structure_parser import IORegStructParser
from sysdiagnose.parsers.iofirewire import IOFireWireParser
from tests import SysdiagnoseTestCase
import unittest
import io
import os


class TestParsersIOFireWire(SysdiagnoseTestCase):

    def test_parse_case(self):
        for case_id, case in self.sd.cases().items():
            p = IOFireWireParser(self.sd.config, case_id=case_id)
            files = p.get_log_files()
            self.assertTrue(len(files) > 0)

            p.save_result(force=True)
            self.assertTrue(os.path.isfile(p.output_file))

    def test_basic_structure(self):
        p = IORegStructParser()

        # careful, spaces and structure is important
        # This simulates an open file object, as if we opened it with open(path, 'rb')
        start_file = io.StringIO("""+-o Root node <class test1, key1 val1>
  | {
  |   "data 1" = "value 1"
  |   "data 2" = "value 2"
  | }
  | 
  +-o Node 2 <class test2, key2 val2>
    | {
    |   "#address-cells" = <02000000>
    |   "AAPL,phandle" = <01000000> 
    | }
    | 
    +-o Node 3 <class test3, key3 val3>
    | | {
    | |   "data 31" = "value 31"
    | |   "data 32" = "value 32"
    | | }
    | | 
    | +-o Leaf 1 <class test11, key11 val11>
    | | {
    | |   "data l1" = "value l1"
    | |   "data l2" = "value l2"
    | | }
    | |
    | +-o Leaf 2 <class test22, key22 val22>
    |   {
    |     "data l3" = "value l3"
    |     "data l4" = "value l4"
    |   }
    | 
    +-o Leaf 3 <class test33, key33 val33>
    | {
    |   "data l5" = "value L5"
    |   "data l6" = "value l6"
    | }
    |
    +-o Leaf 4 <class test44, key44 val44>
        {
          "data 51" = "value 51"
          "data 52" = "value 52"
        }
        
""")  # noqa: W291, W293

        expected = {
            'class': 'test1',
            'key1': 'val1',
            'data 1': 'value 1',
            'data 2': 'value 2',
            'Node 2': {
                'class': 'test2',
                'key2': 'val2',
                '#address-cells': '<02000000>',
                'AAPL,phandle': '<01000000>',
                'Node 3': {
                    'class': 'test3',
                    'key3': 'val3',
                    'data 31': 'value 31',
                    'data 32': 'value 32',
                    'Leaf 1': {
                        'class': 'test11',
                        'key11': 'val11',
                        'data l1': 'value l1',
                        'data l2': 'value l2'
                    },
                    'Leaf 2': {
                        'class': 'test22',
                        'key22': 'val22',
                        'data l3': 'value l3',
                        'data l4': 'value l4'
                    }
                },
                'Leaf 3': {
                    'class': 'test33',
                    'key33': 'val33',
                    'data l5': 'value L5',
                    'data l6': 'value l6'
                },
                'Leaf 4': {
                    'class': 'test44',
                    'key44': 'val44',
                    'data 51': 'value 51',
                    'data 52': 'value 52'
                }
            }
        }

        p.open_file = start_file
        result = {}
        p.recursive_fun(result)

        self.assertTrue(result == expected)

    def test_value_overflow_anomaly(self):
        p = IORegStructParser()

        # careful, spaces and structure is important
        # This simulates an open file object, as if we opened it with open(path, 'rb')
        start_file = io.StringIO("""+-o Root node <class test1, key1 val1>
  | {
  |   "data 1" = "value 1"
  |   "data 2" = "value 2"
  | }
  | 
  +-o Node 2 <class test2, key2 val2>
    | {
    |   "#address-cells" = <02000000>
    |   "AAPL,phandle" = <01000000> 
    | }
    | 
    +-o Node 3 <class test3, key3 val3>
    | | {
    | |   "data 31" = "value 31"
    | |   "data 32" = "value 32"
    | | }
    | | 
    | +-o Leaf 1 <class test11, key11 val11>
    | | {
    | |   "data l1" = "value l1"
    | |   "data l2" = "value l2"
    | | }
    | |
    | +-o Leaf 2 <class test22, key22 val22>
    |   {
    |     "data l3" = "value l3"
    |     "data l4" = "value aaaa
bbbb
cccc
dddd
"
    |   }
    | 
    +-o Leaf 3  <class test33, key33 val33>
    | {
    |   "data l5" = "value L5"
    |   "data l6" = "value l6"
    | }
    |
    +-o Leaf 4 <class test44, key44 val44>
        {
          "data 51" = "value 51"
          "data 52" = "value 52"
        }
        
""")  # noqa: W291, W293

        expected = {
            'class': 'test1',
            'key1': 'val1',
            'data 1': 'value 1',
            'data 2': 'value 2',
            'Node 2': {
                'class': 'test2',
                'key2': 'val2',
                '#address-cells': '<02000000>',
                'AAPL,phandle': '<01000000>',
                'Node 3': {
                    'class': 'test3',
                    'key3': 'val3',
                    'data 31': 'value 31',
                    'data 32': 'value 32',
                    'Leaf 1': {
                        'class': 'test11',
                        'key11': 'val11',
                        'data l1': 'value l1',
                        'data l2': 'value l2'
                    },
                    'Leaf 2': {
                        'class': 'test22',
                        'key22': 'val22',
                        'data l3': 'value l3',
                        'data l4': 'value aaaabbbbccccdddd'
                    }
                },
                'Leaf 3': {
                    'class': 'test33',
                    'key33': 'val33',
                    'data l5': 'value L5',
                    'data l6': 'value l6'
                },
                'Leaf 4': {
                    'class': 'test44',
                    'key44': 'val44',
                    'data 51': 'value 51',
                    'data 52': 'value 52'
                }
            }
        }

        p.open_file = start_file
        result = {}
        p.recursive_fun(result)

        self.assertTrue(result == expected)

    def test_non_ascii_byte_anomaly(self):
        p = IORegStructParser()

        # careful, spaces and structure is important
        # This simulates an open file object, as if we opened it with open(path, 'rb')
        start_file = io.StringIO("""+-o Root node <class test1, key1 val1>
  | {
  |   "data 1" = "value 1"
  |   "data 2" = "value 2"
  | }
  | 
  +-o Node 2 <class test2, key2 val2>
    | {
    |   "#address-cells" = <02000000>
    |   "AAPL,phandle" = <01000000> 
    | }
    | 
    +-o Node 3 <class test3, key3 val3>
    | | {
    | |   "data 31" = "value 31"
    | |   "data 32" = "value 32"
    | | }
    | | 
    | +-o Leaf 1 <class test11, key11 val11>
    | | {
    | |   "data l1" = "value l1"
    | |   "data l2" = "value l2"
    | | }
    | |
    | +-o Leaf 2 <class test22, key22 val22>
    |   {
    |     "data l3" = "value l3"
    |     "data l4" = "value -->\xbf<--"
    |   }
    | 
    +-o Leaf 3 <class test33, key33 val33>
    | {
    |   "data l5" = "value L5"
    |   "data l6" = "value l6"
    | }
    |
    +-o Leaf 4 <class test44, key44 val44>
        {
          "data 51" = "value 51"
          "data 52" = "value 52"
        }
        
""")  # noqa: W291, W293

        expected = {
            'class': 'test1',
            'key1': 'val1',
            'data 1': 'value 1',
            'data 2': 'value 2',
            'Node 2': {
                'class': 'test2',
                'key2': 'val2',
                '#address-cells': '<02000000>',
                'AAPL,phandle': '<01000000>',
                'Node 3': {
                    'class': 'test3',
                    'key3': 'val3',
                    'data 31': 'value 31',
                    'data 32': 'value 32',
                    'Leaf 1': {
                        'class': 'test11',
                        'key11': 'val11',
                        'data l1': 'value l1',
                        'data l2': 'value l2'
                    },
                    'Leaf 2': {
                        'class': 'test22',
                        'key22': 'val22',
                        'data l3': 'value l3',
                        'data l4': 'value -->\xbf<--'
                    }
                },
                'Leaf 3': {
                    'class': 'test33',
                    'key33': 'val33',
                    'data l5': 'value L5',
                    'data l6': 'value l6'
                },
                'Leaf 4': {
                    'class': 'test44',
                    'key44': 'val44',
                    'data 51': 'value 51',
                    'data 52': 'value 52'
                }
            }
        }

        p.open_file = start_file
        result = {}
        p.recursive_fun(result)

        self.assertTrue(result == expected)


if __name__ == '__main__':
    unittest.main()
