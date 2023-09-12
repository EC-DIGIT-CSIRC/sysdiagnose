
from unittest.mock import patch, mock_open
from parsers.sysdiagnose_accessibility_tcc import get_accessibility_tcc         # (dbpath, parse_accessibility_tcc_logs


def test_get_accessibility_tcc():
    mock_file_content = "Line1\nAccessibility Line2\nLine3\nAccessibility Line4"
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        result = get_accessibility_tcc("mock_file_path")
    assert result == ["Accessibility Line2", "Accessibility Line4"]


def test_parse_accessibility_tcc_logs_file_not_found():
    with patch("builtins.open", mock_open()) as mock_file:
        mock_file.side_effect = FileNotFoundError
        result = get_accessibility_tcc("mock_file_path")
    assert result == "File not found"
