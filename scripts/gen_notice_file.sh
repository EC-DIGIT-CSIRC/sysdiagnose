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

EOF
cat "$temp_dir/notice_body.txt" >> "$notice_file"

# clean up
deactivate
echo "Cleaning up temporary directory: $temp_dir"
rm -rf "$temp_dir"

echo
echo "Generated notice file at: $notice_file"
