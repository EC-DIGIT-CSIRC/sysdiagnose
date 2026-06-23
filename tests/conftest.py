def pytest_collection_modifyitems(items):
    """Run parser tests before analyser tests to benefit from cached parsed data."""
    parser_tests = [t for t in items if "test_parsers" in t.nodeid]
    analyser_tests = [t for t in items if "test_analysers" in t.nodeid]
    other_tests = [t for t in items if "test_parsers" not in t.nodeid and "test_analysers" not in t.nodeid]
    items[:] = parser_tests + other_tests + analyser_tests
