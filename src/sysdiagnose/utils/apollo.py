'''
--------------------------------------------------------------------------------
      Copyright (c) 2018-2020 Sarah Edwards (Station X Labs, LLC,
      @iamevltwin, mac4n6.com). All rights reserved.

      Modified by Christophe Vandeplas - 2024

      This software is provided "as is," without warranty of any kind,
      express or implied.  In no event shall the author or contributors
      be held liable for any damages arising in any way from the use of
      this software.

      The contents of this file are DUAL-LICENSED.  You may modify and/or
      redistribute this software according to the terms of one of the
      following two licenses (at your option):

      LICENSE 1 ("BSD-like with acknowledgment clause"):

      Permission is granted to anyone to use this software for any purpose,
      including commercial applications, and to alter it and redistribute
      it freely, subject to the following restrictions:

      1. Redistributions of source code must retain the above copyright
         notice, disclaimer, and this list of conditions.
      2. Redistributions in binary form must reproduce the above copyright
         notice, disclaimer, and this list of conditions in the documenta-
         tion and/or other materials provided with the distribution.
      3. All advertising, training, and documentation materials mentioning
         features or use of this software must display the following
         acknowledgment. Character-limited social media may abbreviate this
         acknowledgment to include author and APOLLO name ie: "This new
         feature brought to you by @iamevltwin's APOLLO". Please make an
         effort credit the appropriate authors on specific APOLLO modules.
         The spirit of this clause is to give public acknowledgment to
         researchers where credit is due.

            This product includes software developed by Sarah Edwards
            (Station X Labs, LLC, @iamevltwin, mac4n6.com) and other
            contributors as part of APOLLO (Apple Pattern of Life Lazy
            Output'er).


      LICENSE 2 (GNU GPL v3 or later):

      This file is part of APOLLO (Apple Pattern of Life Lazy Output'er).

      APOLLO is free software: you can redistribute it and/or modify
      it under the terms of the GNU General Public License as published by
      the Free Software Foundation, either version 3 of the License, or
      (at your option) any later version.

      APOLLO is distributed in the hope that it will be useful,
      but WITHOUT ANY WARRANTY; without even the implied warranty of
      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
      GNU General Public License for more details.

      You should have received a copy of the GNU General Public License
      along with APOLLO.  If not, see <https://www.gnu.org/licenses/>.
--------------------------------------------------------------------------------
'''
import sqlite3
import os
import configparser
import re
from datetime import datetime, timezone
import glob

default_mod_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apollo_modules')


class Apollo():
    def __init__(self, mod_dir: str = default_mod_dir, os_version: str = 'yolo'):
        """
        Initialize the Apollo class for parsing databases

        Args:
            mod_dir (str): The directory where the module definitions are stored
            os_version (str): The version of the OS for which to parse the modules. 'yolo' means all versions.
        """
        self.os_version = os_version
        self.mod_dir = mod_dir

        self.supported_database_names = set()
        self.mod_info = {}
        self.modules: dict[list[dict]] = {}  # dict: db_type -> list of modules
        self.parse_module_definition(mod_dir=self.mod_dir, os_version=self.os_version)

    def parse_module_definition(self, mod_dir, os_version):
        # Parse all module data and build our own list
        mod_files = glob.glob(os.path.join(mod_dir, '*.txt'))
        for mod_file in mod_files:
            parser = configparser.ConfigParser()
            parser.read(mod_file)

            query_name = parser['Query Metadata']['QUERY_NAME']
            activity = parser['Query Metadata']['ACTIVITY']
            key_timestamp = parser['Query Metadata']['KEY_TIMESTAMP']
            databases = parser['Database Metadata']['DATABASE']
            database_name = databases.split(',')

            for db in database_name:
                # old code
                self.supported_database_names.add(db)  # keep track of supported databases

                for section in parser.sections():
                    if 'SQL Query' not in section:
                        continue
                    if os_version == 'yolo' or os_version in re.split('[ ,]', section):
                        sql_query = parser.items(section, 'QUERY')[0][1]
                        if db not in self.modules:
                            self.modules[db] = []
                        self.modules[db].append({
                            'name': query_name,
                            'db': db,
                            'activity': activity,
                            'key_timestamp': key_timestamp,
                            'sql': sql_query
                        })

    def parse_db(self, db_fname: str, db_type: str = None) -> list:
        results = []
        if not db_type:
            db_type = os.path.basename(db_fname)

        try:
            module_queries = self.modules[db_type]
        except KeyError:
            print(f"No modules with queries for {db_type}.")
            return results

        # establish db connection
        conn = sqlite3.connect(db_fname)
        with conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

        # now do all the queries for this db
        for module_query in module_queries:
            try:
                cur.execute(module_query['sql'])
                rows = cur.fetchall()
            except Exception:
                print(f"ERROR: Cannot fetch query contents for {module_query['name']}.")
                continue

            if not rows:
                print(f"No Records Found for {module_query['name']}.")
                continue

            headers = []
            for x in cur.description:
                headers.append(x[0].lower())

            key_timestamp = module_query['key_timestamp'].lower()
            for row in rows:
                item = dict(list(zip(headers, row)))
                try:
                    timestamp = datetime.fromisoformat(item[key_timestamp])
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                    item['timestamp'] = timestamp.timestamp()
                    item['datetime'] = timestamp.isoformat(timespec='microseconds')
                    item['module_name'] = module_query['name']
                    item['module_activity'] = module_query['activity']
                    results.append(item)
                except TypeError:
                    # problem with timestamp parsing
                    print(f"WARNING: Problem with timestamp parsing for table {db_fname}, row {list(row)}")

        print("Executing module on: " + db_fname)
        return results