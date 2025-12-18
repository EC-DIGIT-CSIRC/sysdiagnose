from tests import SysdiagnoseTestCase
import unittest
import sysdiagnose.utils.string_parser as sp


class TestStringParser(SysdiagnoseTestCase):

    test_list = [
        '[hello world]',
        '<this_is_[not a struct]_here>',
        '<key val, k2 v2>',
        '(li1, li2, li3, li4)',
        '< k1     v1  ,  k2 v2,   k3    v3      ,k4 v4    >',
        '<k1 <k11 v11>>',
        '(    li 1, li   2   , li3)',
        '<k1 v1, k2 v2, k:3 (li1 , li2 ,li3, li4 )  ,k4 v4 >',
        '<k1 v1, k2 (li1 , li2 ,li3, li4 )  ,k3 (li11, li22)     , k4 (li111, li222, li333) >',
        '<k1 v1, k2 (li1 , li2,li3, li4 )  ,k3 <k11 v11,k22 v22>     , k4 (li111, li222, li333) >',
        '<l (1, 2, <k (,,,)>), m <g (), k ( ,), m ((),(()))>>',
        '<k1 v1, k2 <k11 v11, k22 v22>  ,k3 (<k111 <a b, c (l1, l2)>>, (li111), (li8, li9))    , k4 (li111, li222, li333) >',
        '<"!!J>">'
    ]

    expected_parsed = [
        "[hello world]",
        '<this_is_[not a struct]_here>',
        {'key': 'val', 'k2': 'v2'},
        ['li1', 'li2', 'li3', 'li4'],
        {'k1': 'v1', 'k2': 'v2', 'k3': 'v3', 'k4': 'v4'},
        {'k1': {'k11': 'v11'}},
        ['li 1', 'li   2', 'li3'],
        {'k1': 'v1', 'k2': 'v2', 'k:3': ['li1', 'li2', 'li3', 'li4'], 'k4': 'v4'},
        {'k1': 'v1', 'k2': ['li1', 'li2', 'li3', 'li4'], 'k3': ['li11', 'li22'], 'k4': ['li111', 'li222', 'li333']},
        {'k1': 'v1', 'k2': ['li1', 'li2', 'li3', 'li4'], 'k3': {'k11': 'v11', 'k22': 'v22'}, 'k4': ['li111', 'li222', 'li333']},
        {'l': ['1', '2', {'k': ['', '', '', '']}], 'm': {'g': '()', 'k': ['', ''], 'm': ['()', '(())']}},
        {'k1': 'v1', 'k2': {'k11': 'v11', 'k22': 'v22'}, 'k3': [{'k111': {'a': 'b', 'c': ['l1', 'l2']}}, '(li111)', ['li8', 'li9']], 'k4': ['li111', 'li222', 'li333']},
        '<"!!J>">'
    ]

    def test_parsing(self):
        for test_val, expected in zip(self.test_list, self.expected_parsed):
            result = sp.Parser().parse(test_val)
            self.assertTrue(result == expected)


if __name__ == '__main__':
    unittest.main()
