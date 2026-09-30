import json
import logging
import os
import sqlite3
import tempfile
import unittest

from sysdiagnose.utils.apollo import Apollo


class TestApolloBlob(unittest.TestCase):
    """sqlite BLOB columns must not reach json.dumps as raw bytes."""

    def _build_db_and_module(self, tmp):
        db_path = os.path.join(tmp, "test.db")
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE t (ts TEXT, payload BLOB)")
        con.execute("INSERT INTO t VALUES (?, ?)", ("2023-05-24 13:29:15", b"\x89PNG\r\n\x1a\n\xff\xfe"))
        con.commit()
        con.close()

        mod_dir = os.path.join(tmp, "modules")
        os.makedirs(mod_dir)
        with open(os.path.join(mod_dir, "test.txt"), "w") as f:
            f.write(
                "[Module Metadata]\n"
                "AUTHOR = test\n"
                "MODULE_NAME = test_module\n"
                "LAST_UPDATED = 2024-01-01\n"
                "\n"
                "[Database Metadata]\n"
                "DATABASE = test.db\n"
                "\n"
                "[Query Metadata]\n"
                "QUERY_NAME = test_query\n"
                "ACTIVITY = test activity\n"
                "KEY_TIMESTAMP = ts\n"
                "\n"
                "[SQL Query 14.0]\n"
                "QUERY = \n"
                "    SELECT ts, payload FROM t\n"
            )
        return db_path, mod_dir

    def test_blob_column_is_json_serialisable(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path, mod_dir = self._build_db_and_module(tmp)
            a = Apollo(
                logger=logging.getLogger("test"),
                saf_module="test",
                mod_dir=mod_dir,
                os_version="14.0",
            )
            results = a.parse_db(db_fname=db_path, db_type="test.db")

        self.assertTrue(results, "expected at least one event")
        # on main this raises TypeError: Object of type bytes is not JSON serializable
        json.dumps(results)


if __name__ == "__main__":
    unittest.main()
