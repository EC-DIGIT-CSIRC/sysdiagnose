#!/bin/bash
# Generate the notice file for the project. This file contains the licenses of all dependencies.

# To know which files are required for the notice file we install the dependencies in a clean
# environment and run the command to generate the notice file. We then check which files are
# required for the notice file and add them to the .gitignore file.

if ! command -v pip-licenses &> /dev/null; then
    echo
    echo "ERROR: Cannot run generate notice file"
    echo "'pip-licenses' is not installed. Install with: pip install pip-licenses"
    exit 1
fi

# output file is the folder one level higher than this script
root_dir=$(readlink -f "$(dirname "$(dirname "$0")")")
#root_dir=$(dirname "$(dirname "$0")")

notice_file="$root_dir/NOTICE.txt"

# create temporary folder in tmp with venv
temp_dir=$(mktemp -d)
echo "Created temporary directory: $temp_dir"
python -m venv "$temp_dir/venv"
source "$temp_dir/venv/bin/activate"
pip install "$root_dir"

# generate the notice file
pip-licenses -u --format=plain-vertical --with-notice-file --with-license-file --no-license-path --no-version --output-file="$temp_dir/notice_body.txt"

# figure out the current year
year=$(date +"%Y")

# merge header text with the generated notice file
cat <<EOF > "$notice_file"
Sysdiagnose Analysis Framework
========================================================================================
Copyright (C) 2023-$year European Union
Licensed under the EUPL, Version 1.2 or - as soon they will be approved by the European Commission - subsequent versions of the EUPL (the "Licence");
You may not use this work except in compliance with the Licence.

You may obtain a copy of the Licence at: https://joinup.ec.europa.eu/software/page/eupl

Unless required by applicable law or agreed to in writing, software distributed under the
Licence is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
either express or implied.See the Licence for the specific language governing permissions
and limitations under the Licence.

This product depends on software developed by third parties as listed below.
========================================================================================

Apollo
BSD License
https://github.com/mac4n6/APOLLO
Copyright (c) 2018-2020 Sarah Edwards (Station X Labs, LLC, @iamevltwin, mac4n6.com).

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


EOF
cat "$temp_dir/notice_body.txt" >> "$notice_file"

# clean up
deactivate
echo "Cleaning up temporary directory: $temp_dir"
rm -rf "$temp_dir"

echo
echo "Generated notice file at: $notice_file"
