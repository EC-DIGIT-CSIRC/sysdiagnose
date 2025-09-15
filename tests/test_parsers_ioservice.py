from sysdiagnose.parsers.ioservice import IOServiceParser
from tests import SysdiagnoseTestCase
import unittest
import io


class TestParsersIOService(SysdiagnoseTestCase):

    def test_basic_structure(self):
        for case_id, _ in self.sd.cases().items():
            p = IOServiceParser(self.sd.config, case_id=case_id)
        
        # careful, spaces and structure is important
        # This simulates an open file object, as if we opened it with open(path, 'rb')
        start_file = io.BytesIO(b"""+-o Root node
  | {
  |   "data 1" = "value 1"
  |   "data 2" = "value 2"
  | }
  | 
  +-o Node 2
    | {
    |   "#address-cells" = <02000000>
    |   "AAPL,phandle" = <01000000> 
    | }
    | 
    +-o Node 3
    | | {
    | |   "data 31" = "value 31"
    | |   "data 32" = "value 32"
    | | }
    | | 
    | +-o Leaf 1
    | | {
    | |   "data l1" = "value l1"
    | |   "data l2" = "value l2"
    | | }
    | |
    | +-o Leaf 2
    |   {
    |     "data l3" = "value l3"
    |     "data l4" = "value l4"
    |   }
    | 
    +-o Leaf 3
    | {
    |   "data l5" = "value L5"
    |   "data l6" = "value l6"
    | }
    |
    +-o Leaf 4
        {
          "data 51" = "value 51"
          "data 52" = "value 52"
        }
        
""")
        
        expected = {
            "Children": [
                {
                "Children": [
                    {
                    "Children": [
                        {
                        "Children": [],
                        "Data": {
                            "data l1": "\"value l1\"",
                            "data l2": "\"value l2\""
                        },
                        "Name": "Leaf 1"
                        },
                        {
                        "Children": [],
                        "Data": {
                            "data l3": "\"value l3\"",
                            "data l4": "\"value l4\""
                        },
                        "Name": "Leaf 2"
                        }
                    ],
                    "Data": {
                        "data 31": "\"value 31\"",
                        "data 32": "\"value 32\""
                    },
                    "Name": "Node 3"
                    },
                    {
                    "Children": [],
                    "Data": {
                        "data l5": "\"value L5\"",
                        "data l6": "\"value l6\""
                    },
                    "Name": "Leaf 3"
                    },
                    {
                    "Children": [],
                    "Data": {
                        "data 51": "\"value 51\"",
                        "data 52": "\"value 52\""
                    },
                    "Name": "Leaf 4"
                    }
                ],
                "Data": {
                    "#address-cells": "<02000000>",
                    "AAPL,phandle": "<01000000>"
                },
                "Name": "Node 2"
                }
            ],
            "Data": {
                "data 1": "\"value 1\"",
                "data 2": "\"value 2\""
            },
            "Name": "Root node"
        }

        p.open_file = start_file
        result = {}
        p.recursive_fun(result)

        self.assertTrue(result == expected)

    def test_value_overflow_anomaly(self):
        for case_id, _ in self.sd.cases().items():
            p = IOServiceParser(self.sd.config, case_id=case_id)
        
        # careful, spaces and structure is important
        # This simulates an open file object, as if we opened it with open(path, 'rb')
        start_file = io.BytesIO(b"""+-o Root node
  | {
  |   "data 1" = "value 1"
  |   "data 2" = "value 2"
  | }
  | 
  +-o Node 2
    | {
    |   "#address-cells" = <02000000>
    |   "AAPL,phandle" = <01000000> 
    | }
    | 
    +-o Node 3
    | | {
    | |   "data 31" = "value 31"
    | |   "data 32" = "value 32"
    | | }
    | | 
    | +-o Leaf 1
    | | {
    | |   "data l1" = "value l1"
    | |   "data l2" = "value l2"
    | | }
    | |
    | +-o Leaf 2
    |   {
    |     "data l3" = "value l3"
    |     "data l4" = "value aaaa
bbbb
cccc
dddd
"
    |   }
    | 
    +-o Leaf 3
    | {
    |   "data l5" = "value L5"
    |   "data l6" = "value l6"
    | }
    |
    +-o Leaf 4
        {
          "data 51" = "value 51"
          "data 52" = "value 52"
        }
        
""")
        
        expected = {
            "Children": [
                {
                "Children": [
                    {
                    "Children": [
                        {
                        "Children": [],
                        "Data": {
                            "data l1": "\"value l1\"",
                            "data l2": "\"value l2\""
                        },
                        "Name": "Leaf 1"
                        },
                        {
                        "Children": [],
                        "Data": {
                            "data l3": "\"value l3\"",
                            "data l4": "\"value aaaabbbbccccdddd\""
                        },
                        "Name": "Leaf 2"
                        }
                    ],
                    "Data": {
                        "data 31": "\"value 31\"",
                        "data 32": "\"value 32\""
                    },
                    "Name": "Node 3"
                    },
                    {
                    "Children": [],
                    "Data": {
                        "data l5": "\"value L5\"",
                        "data l6": "\"value l6\""
                    },
                    "Name": "Leaf 3"
                    },
                    {
                    "Children": [],
                    "Data": {
                        "data 51": "\"value 51\"",
                        "data 52": "\"value 52\""
                    },
                    "Name": "Leaf 4"
                    }
                ],
                "Data": {
                    "#address-cells": "<02000000>",
                    "AAPL,phandle": "<01000000>"
                },
                "Name": "Node 2"
                }
            ],
            "Data": {
                "data 1": "\"value 1\"",
                "data 2": "\"value 2\""
            },
            "Name": "Root node"
        }

        p.open_file = start_file
        result = {}
        p.recursive_fun(result)

        self.assertTrue(result == expected)

    def test_non_ascii_byte_anomaly(self):
        for case_id, _ in self.sd.cases().items():
            p = IOServiceParser(self.sd.config, case_id=case_id)
        
        # careful, spaces and structure is important
        # This simulates an open file object, as if we opened it with open(path, 'rb')
        start_file = io.BytesIO(b"""+-o Root node
  | {
  |   "data 1" = "value 1"
  |   "data 2" = "value 2"
  | }
  | 
  +-o Node 2
    | {
    |   "#address-cells" = <02000000>
    |   "AAPL,phandle" = <01000000> 
    | }
    | 
    +-o Node 3
    | | {
    | |   "data 31" = "value 31"
    | |   "data 32" = "value 32"
    | | }
    | | 
    | +-o Leaf 1
    | | {
    | |   "data l1" = "value l1"
    | |   "data l2" = "value l2"
    | | }
    | |
    | +-o Leaf 2
    |   {
    |     "data l3" = "value l3"
    |     "data l4" = "value -->\xbf<--"
    |   }
    | 
    +-o Leaf 3
    | {
    |   "data l5" = "value L5"
    |   "data l6" = "value l6"
    | }
    |
    +-o Leaf 4
        {
          "data 51" = "value 51"
          "data 52" = "value 52"
        }
        
""")
        
        expected = {
            "Children": [
                {
                "Children": [
                    {
                    "Children": [
                        {
                        "Children": [],
                        "Data": {
                            "data l1": "\"value l1\"",
                            "data l2": "\"value l2\""
                        },
                        "Name": "Leaf 1"
                        },
                        {
                        "Children": [],
                        "Data": {
                            "data l3": "\"value l3\"",
                            "data l4": "\"value -->?<--\""
                        },
                        "Name": "Leaf 2"
                        }
                    ],
                    "Data": {
                        "data 31": "\"value 31\"",
                        "data 32": "\"value 32\""
                    },
                    "Name": "Node 3"
                    },
                    {
                    "Children": [],
                    "Data": {
                        "data l5": "\"value L5\"",
                        "data l6": "\"value l6\""
                    },
                    "Name": "Leaf 3"
                    },
                    {
                    "Children": [],
                    "Data": {
                        "data 51": "\"value 51\"",
                        "data 52": "\"value 52\""
                    },
                    "Name": "Leaf 4"
                    }
                ],
                "Data": {
                    "#address-cells": "<02000000>",
                    "AAPL,phandle": "<01000000>"
                },
                "Name": "Node 2"
                }
            ],
            "Data": {
                "data 1": "\"value 1\"",
                "data 2": "\"value 2\""
            },
            "Name": "Root node"
        }

        p.open_file = start_file
        result = {}
        p.recursive_fun(result)

        self.assertTrue(result == expected)


if __name__ == '__main__':
    unittest.main()
