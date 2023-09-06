import pytest
from unittest.mock import mock_open, patch
import plistlib
import sys
from parsers.sysdiagnoseSys import getProductInfo


@pytest.fixture
def plist_data():
    return {
        'BuildID': 'XXXXXXXX-AAAA-11ED-A220-A96DC6F47ACD',
        'ProductBuildVersion': '20D69',
        'ProductCopyright': '1983-2023 Apple Inc.',
        'ProductName': 'iPhone OS',
        'ProductVersion': '16.3.1',
        'SystemImageID': 'XXXXXXXX-500F-4C87-8184-E514BC0A1A64'
    }


def test_getProductInfo(plist_data):
    mock_open_obj = mock_open()
    with patch('builtins.open', mock_open_obj):
        with patch.object(plistlib, 'load', return_value=plist_data):
            result = getProductInfo()
            assert result['ProductName'] == 'iPhone OS'
            assert result['ProductVersion'] == '16.3.1'
            assert result['ProductBuildVersion'] == '20D69'


def test_getProductInfo_missing_key(plist_data):
    del plist_data['ProductName']           # example: here we make sure that a missing key is really missing
    mock_open_obj = mock_open()
    with patch('builtins.open', mock_open_obj):
        with patch.object(plistlib, 'load', return_value=plist_data):
            with patch.object(sys, 'stderr'):
                result = getProductInfo()
                assert result['ProductName'] is None
                assert result['ProductVersion'] == '16.3.1'
                assert result['ProductBuildVersion'] == '20D69'
