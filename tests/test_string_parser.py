from tests import SysdiagnoseTestCase
import unittest
import sysdiagnose.utils.ioreg_parsers.string_parser as sp


class TestStringParser(SysdiagnoseTestCase):

    test_list = [
        '<key val, k2 v2>',
        '(li1, li2, li3, li4)',
        '< k1     v1  ,  k2 v2,   k3    v3      ,k4 v4    >',
        '<k1 <k11 v11>>',
        '(    li 1, li   2   , li3)',
        '<k1 v1, k2 v2, k:3 (li1 , li2 ,li3, li4 )  ,k4 v4 >',
        '<k1 v1, k2 (li1 , li2 ,li3, li4 )  ,k3 (li11, li22)     , k4 (li111, li222, li333) >',
        '<k1 v1, k2 (li1 , li2,li3, li4 )  ,k3 <k11 v11,k22 v22>     , k4 (li111, li222, li333) >',
        '<l (1, 2, <k (,,,)>), m <g (), k ( ,), m ((),(()))>>',
        '<k1 v1, k2 <k11 v11, k22 v22>  ,k3 (<k111 <a b, c (l1, l2)>>, (li111), (li8, li9))    , k4 (li111, li222, li333) >'
    ]

    expected_parsed = [
        {'key': 'val', 'k2': 'v2'},
        ['li1', 'li2', 'li3', 'li4'],
        {'k1': 'v1', 'k2': 'v2', 'k3': 'v3', 'k4': 'v4'},
        {'k1': {'k11': 'v11'}},
        ['li 1', 'li   2', 'li3'],
        {'k1': 'v1', 'k2': 'v2', 'k:3': ['li1', 'li2', 'li3', 'li4'], 'k4': 'v4'},
        {'k1': 'v1', 'k2': ['li1', 'li2', 'li3', 'li4'], 'k3': ['li11', 'li22'], 'k4': ['li111', 'li222', 'li333']},
        {'k1': 'v1', 'k2': ['li1', 'li2', 'li3', 'li4'], 'k3': {'k11': 'v11', 'k22': 'v22'}, 'k4': ['li111', 'li222', 'li333']},
        {'l': ['1', '2', {'k': ['', '', '', '']}], 'm': {'g': '()', 'k': ['', ''], 'm': ['()', '(())']}},
        {'k1': 'v1', 'k2': {'k11': 'v11', 'k22': 'v22'}, 'k3': [{'k111': {'a': 'b', 'c': ['l1', 'l2']}}, '(li111)', ['li8', 'li9']], 'k4': ['li111', 'li222', 'li333']}
    ]

    expected_detect = [
        ('key val, k2 v2', sp.DataType.XML_LIKE),
        ('li1, li2, li3, li4', sp.DataType.LIST),
        (' k1     v1  ,  k2 v2,   k3    v3      ,k4 v4    ', sp.DataType.XML_LIKE),
        ('k11 v11', sp.DataType.XML_LIKE),
        ('    li 1, li   2   , li3', sp.DataType.LIST),
        ('li1 , li2 ,li3, li4 ', sp.DataType.LIST),
        ('li1 , li2 ,li3, li4 ', sp.DataType.LIST),
        ('k11 v11,k22 v22', sp.DataType.XML_LIKE),
        ('()', sp.DataType.STRING),
        ('(li111)', sp.DataType.STRING)
    ]

    def test_detect(self):
        for test_val, (exp_cont, exp_type) in zip(self.test_list, self.expected_detect):
            d = sp.Detect(test_val)
            self.assertTrue(d.content == exp_cont)
            self.assertTrue(d.type == exp_type)

    def test_parsing(self):
        for test_val, expected in zip(self.test_list, self.expected_parsed):
            result = sp.parse(test_val)
            self.assertTrue(result == expected)


if __name__ == '__main__':
    unittest.main()
