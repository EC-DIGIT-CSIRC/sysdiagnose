import argparse
import json
from jinja2 import Template


def load_json(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def compare_file_stats_sysdiag_properties(obj1: dict, obj2: dict) -> tuple[dict, dict, dict]:
    """
        Compare the properties section of the file_stats JSON files and return added, removed, and modified fields.

        :param obj1: First JSON object (dictionary).
        :param obj2: Second JSON object (dictionary).
        :return: A dictionary with added, removed, and modified fields.
    """
    # Identify added and removed keys
    added = {key: obj2[key] for key in obj2 if key not in obj1}
    removed = {key: obj1[key] for key in obj1 if key not in obj2}

    # Identify modified keys
    modified = {
        key: {"old_value": obj1[key], "new_value": obj2[key]}
        for key in obj1.keys() & obj2.keys()  # Intersection of keys
        if obj1[key] != obj2[key]
    }

    return added, removed, modified

def compare_file_stats_folders_details(arr1: list[dict], arr2: list[dict],
                                       exclusions: list[str] = None) -> tuple[list, list, list]:
    """
        Efficiently compare two arrays of dictionaries using a unique key, with exclusions.

        :param arr1: First array of dictionaries.
        :param arr2: Second array of dictionaries.
        :param unique_key: The key used to uniquely identify each dictionary.
        :param exclusions: A list of folder name substrings to exclude from the comparison.
        :return: Added, removed, and modified items.
    """
    unique_key = "folder_name"
    exclusions = exclusions or []  # Default to an empty list if no exclusions are provided

    # Filter out excluded folders based on substring match
    def is_excluded(folder_name):
        return any(exclusion in folder_name for exclusion in exclusions)

    arr1 = [item for item in arr1 if not is_excluded(item[unique_key])]
    arr2 = [item for item in arr2 if not is_excluded(item[unique_key])]

    # Index the arrays by the unique key for quick lookup
    index1 = {item[unique_key]: item for item in arr1}
    index2 = {item[unique_key]: item for item in arr2}

    # Identify added and removed items
    added = [item for key, item in index2.items() if key not in index1]
    removed = [item for key, item in index1.items() if key not in index2]

    # Identify modified items
    modified = []
    for key in index1.keys() & index2.keys():  # Intersection of keys
        item1 = index1[key]
        item2 = index2[key]
        if item1 != item2:  # Check if the items are different
            file_diff = {
                "folder_name": key,
                "file_count_diff": (item1.get("file_count"), item2.get("file_count")),
                "files_diff": {
                    "added": [f for f in item2.get("files", []) if f not in item1.get("files", [])],
                    "removed": [f for f in item1.get("files", []) if f not in item2.get("files", [])],
                    "modified": [
                        (f1, f2)
                        for f1 in item1.get("files", [])
                        for f2 in item2.get("files", [])
                        if f1["filename"] == f2["filename"] and f1 != f2
                    ],
                },
            }
            modified.append(file_diff)

    return added, removed, modified

def generate_html_report(added_properties: dict, removed_properties: dict, modified_properties: dict,
                         added: list, removed: list, modified: list, exclusions: list, output_file: str) -> None:
    """
        Generate an HTML report using Jinja2.
        :param added_properties: Added properties.
        :param removed_properties: Removed properties.
        :param modified_properties: Modified properties.
        :param added: Added folders.
        :param removed: Removed folders.
        :param modified: Modified folders.
        :param exclusions: List of excluded folder substrings.
        :param output_file: Output HTML file path.
    """

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sysdiagnose file statistics comparison</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            .added { background-color: #d4f8d4; border: 1px solid #a3e6a3; padding: 10px; margin-bottom: 10px; border-radius: 8px; }
            .removed { background-color: #f8d4d4; border: 1px solid #e6a3a3; padding: 10px; margin-bottom: 10px; border-radius: 8px; }
            .modified { background-color: #f8f4d4; border: 1px solid #e6e3a3; padding: 10px; margin-bottom: 10px; border-radius: 8px; }
            .excluded { background-color: #f0f0f0; border: 1px solid #666666; padding: 10px; margin-bottom: 10px; border-radius: 8px; }
            .collapsible { cursor: pointer; padding: 10px; border: none; text-align: left; outline: none; font-size: 16px; font-weight: bold; }
            .collapsible.added { color: #2e7d32; } /* Dark green for added */
            .collapsible.removed { color: #c62828; } /* Dark red for removed */
            .collapsible.modified { color: #f9a825; } /* Dark yellow for modified */
            .collapsible.excluded { color: #666666; } /* Grey for excluded */
            .content { display: none; padding: 10px; border: 1px solid #ccc; margin-top: 5px; border-radius: 8px; }
            table { border-collapse: collapse; width: 100%; margin-top: 10px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { cursor: pointer; } /* Make headers clickable */
            th.added { background-color: #2e7d32; color: white; } /* Dark green for added table headers */
            th.removed { background-color: #c62828; color: white; } /* Dark red for removed table headers */
            th.modified { background-color: #f9a825; color: black; } /* Dark yellow for modified table headers */
        </style>
        <script>
            function toggleContent(id) {
                var content = document.getElementById(id);
                if (content.style.display === "none" || content.style.display === "") {
                    content.style.display = "block";
                } else {
                    content.style.display = "none";
                }
            }

            function sortTable(tableId, columnIndex) {
                {% raw %}
                var regex = /[\\s\\-\\^v]+$/; // Escaped backslashes for Python string
                {% endraw %}
                var table = document.getElementById(tableId);
                var rows = Array.from(table.rows).slice(1); // Exclude header row
                var isAscending = table.getAttribute("data-sort-order") !== "asc";

                rows.sort(function(rowA, rowB) {
                    var cellA = rowA.cells[columnIndex].innerText.trim();
                    var cellB = rowB.cells[columnIndex].innerText.trim();

                    // Check if the values are numeric
                    var numA = parseFloat(cellA);
                    var numB = parseFloat(cellB);

                    if (!isNaN(numA) && !isNaN(numB)) {
                        // Numeric comparison
                        return isAscending ? numA - numB : numB - numA;
                    } else {
                        // String comparison
                        return isAscending ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
                    }
                });

                // Append sorted rows back to the table
                rows.forEach(function(row) { table.tBodies[0].appendChild(row); });

                // Update sort order attribute
                table.setAttribute("data-sort-order", isAscending ? "asc" : "desc");

                // Update header icons
                var headers = table.querySelectorAll("th");
                headers.forEach(function(header, index) {
                    if (index === columnIndex) {
                        header.innerHTML = header.innerText.replace(regex, "") + (isAscending ? " ^" : " v");
                    } else {
                        header.innerHTML = header.innerText.replace(regex, "") + " -"; // Reset to dot
                    }
                });
            }

            // Automatically sort all tables by the first column on page load
            window.onload = function() {
                var tables = document.querySelectorAll("table");
                tables.forEach(function(table) {
                    if (table.id) { // Ensure the table has an ID
                        sortTable(table.id, 0); // Sort by the first column (index 0)
                    }
                });
            };
        </script>
    </head>
    <body>
        <h1>Sysdiagnose file statistics comparison</h1>

        <h2>Device and OS Differences</h2>

        <!-- Added Properties Section -->
        <div class="added">
            <h2 class="collapsible added" onclick="toggleContent('added-properties')">Added Properties ({{ added_properties|length }})</h2>
            <div id="added-properties" class="content">
                {% if added_properties %}
                <table>
                    <tr>
                        {% for key in added_properties.keys() %}
                            <th class="added">{{ key }}</th>
                        {% endfor %}
                    </tr>
                    <tr>
                        {% for value in added_properties.values() %}
                            <td>{{ value }}</td>
                        {% endfor %}
                    </tr>
                </table>
                {% else %}
                <p>No added properties.</p>
                {% endif %}
            </div>
        </div>

        <!-- Removed Properties Section -->
        <div class="removed">
            <h2 class="collapsible removed" onclick="toggleContent('removed-properties')">Removed Properties ({{ removed_properties|length }})</h2>
            <div id="removed-properties" class="content">
                {% if removed_properties %}
                <table>
                    <tr>
                        {% for key in removed_properties.keys() %}
                            <th class="removed">{{ key }}</th>
                        {% endfor %}
                    </tr>
                    <tr>
                        {% for value in removed_properties.values() %}
                            <td>{{ value }}</td>
                        {% endfor %}
                    </tr>
                </table>
                {% else %}
                <p>No removed properties.</p>
                {% endif %}
            </div>
        </div>

        <!-- Modified Properties Section -->
        <div class="modified">
            <h2 class="collapsible modified" onclick="toggleContent('modified-properties')">Modified Properties ({{ modified_properties|length }})</h2>
            <div id="modified-properties" class="content">
                {% if modified_properties %}
                <table>
                    <tr>
                        <th class="modified">Property</th>
                        <th class="modified">Old Value</th>
                        <th class="modified">New Value</th>
                    </tr>
                    {% for key, value in modified_properties.items() %}
                    <tr>
                        <td>{{ key }}</td>
                        <td>{{ value.old_value }}</td>
                        <td>{{ value.new_value }}</td>
                    </tr>
                    {% endfor %}
                </table>
                {% else %}
                <p>No modified properties.</p>
                {% endif %}
            </div>
        </div>

        <h2>Folders Differences</h2>

        <!-- Exclusions Section -->
        <div class="excluded">
            <h2 class="collapsible excluded" onclick="toggleContent('excluded-folders')">Excluded Folders ({{ exclusions|length }})</h2>
            <div id="excluded-folders" class="content">
                {% if exclusions %}
                <ul>
                    {% for exclusion in exclusions %}
                    <li>{{ exclusion }}</li>
                    {% endfor %}
                </ul>
                {% else %}
                <p>No exclusions applied.</p>
                {% endif %}
            </div>
        </div>


        <!-- Added Folders Section -->
        <div class="added">
            <h2 class="collapsible added" onclick="toggleContent('added-folders')">Added Folders ({{ added|length }})</h2>
            <div id="added-folders" class="content">
                {% if added %}
                <table id="addedTable" data-sort-order="asc">
                    <tr>
                        <th class="added" onclick="sortTable('addedTable', 0)">Folder</th>
                        <th class="added" onclick="sortTable('addedTable', 1)">Files</th>
                    </tr>
                    {% for folder in added %}
                    <tr>
                        <td>{{ folder.folder_name }}</td>
                        <td>{{ folder.file_count }}</td>
                    </tr>
                    {% endfor %}
                </table>
                {% else %}
                <p>No added folders.</p>
                {% endif %}
            </div>
        </div>

        <!-- Removed Folders Section -->
        <div class="removed">
            <h2 class="collapsible removed" onclick="toggleContent('removed-folders')">Removed Folders ({{ removed|length }})</h2>
            <div id="removed-folders" class="content">
                {% if removed %}
                <table id="removedTable" data-sort-order="asc">
                    <tr>
                        <th class="removed" onclick="sortTable('removedTable', 0)">Folder</th>
                        <th class="removed" onclick="sortTable('removedTable', 1)">Files</th>
                    </tr>
                    {% for folder in removed %}
                    <tr>
                        <td>{{ folder.folder_name }}</td>
                        <td>{{ folder.file_count }}</td>
                    </tr>
                    {% endfor %}
                </table>
                {% else %}
                <p>No removed folders.</p>
                {% endif %}
            </div>
        </div>

        <!-- Modified Folders Section -->
        <div class="modified">
            <h2 class="collapsible modified" onclick="toggleContent('modified-folders')">Modified Folders ({{ modified|length }})</h2>
            <div id="modified-folders" class="content">
                {% if modified %}
                <table id="modifiedTable" data-sort-order="asc">
                    <tr>
                        <th class="modified" onclick="sortTable('modifiedTable', 0)">Folder</th>
                        <th class="modified" onclick="sortTable('modifiedTable', 1)">Old Files</th>
                        <th class="modified" onclick="sortTable('modifiedTable', 2)">New Files</th>
                    </tr>
                    {% for folder in modified %}
                    <tr>
                        <td>{{ folder.folder_name }}</td>
                        <td>{{ folder.file_count_diff[0] }}</td>
                        <td>{{ folder.file_count_diff[1] }}</td>
                    </tr>
                    {% endfor %}
                </table>

                <!-- Detailed Sections -->
                {% for folder in modified %}
                    {% if folder.files_diff.modified %}
                    <h3>{{ folder.folder_name }}</h3>
                    <table id="detailsTable_{{ loop.index }}" data-sort-order="asc">
                        <tr>
                            <th class="modified" onclick="sortTable('detailsTable_{{ loop.index }}', 0)">File</th>
                            <th class="modified" onclick="sortTable('detailsTable_{{ loop.index }}', 1)">Old Type</th>
                            <th class="modified" onclick="sortTable('detailsTable_{{ loop.index }}', 2)">New Type</th>
                        </tr>
                        {% for file_pair in folder.files_diff.modified %}
                        <tr>
                            <td>{{ file_pair[0].filename }}</td>
                            <td>{{ file_pair[0].file_type }}</td>
                            <td>{{ file_pair[1].file_type }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                    {% endif %}
                {% endfor %}
                {% else %}
                <p>No modified folders.</p>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    """
    template = Template(html_template)
    rendered_html = template.render(
        added_properties=added_properties,
        removed_properties=removed_properties,
        modified_properties=modified_properties,
        added=added,
        removed=removed,
        modified=modified,
        exclusions=exclusions
    )

    with open(output_file, 'w') as file:
        file.write(rendered_html)

def generate_markdown_report(added_properties: dict, removed_properties: dict, modified_properties: dict,
                             added: list, removed: list, modified: list, exclusions: list, output_file: str) -> None:
    """
        Generate a Markdown report.
        :param added_properties: Added properties.
        :param removed_properties: Removed properties.
        :param modified_properties: Modified properties.
        :param added: Added folders.
        :param removed: Removed folders.
        :param modified: Modified folders.
        :param exclusions: List of excluded folder substrings.
        :param output_file: Output Markdown file path.
    """
    markdown_content = []

    # Title
    markdown_content.append("# Sysdiagnose File Statistics Comparison\n")

    # Device and OS Differences
    markdown_content.append("## Device and OS Differences\n")

    # Added Properties
    markdown_content.append(f"### Added Properties ({len(added_properties)})\n")
    if added_properties:
        markdown_content.append("| Property | Value |\n|----------|-------|")
        for key, value in added_properties.items():
            markdown_content.append(f"| {key} | {value} |")
    else:
        markdown_content.append("No added properties.\n")

    # Removed Properties
    markdown_content.append(f"### Removed Properties ({len(removed_properties)})\n")
    if removed_properties:
        markdown_content.append("| Property | Value |\n|----------|-------|")
        for key, value in removed_properties.items():
            markdown_content.append(f"| {key} | {value} |")
    else:
        markdown_content.append("No removed properties.\n")

    # Modified Properties
    markdown_content.append(f"### Modified Properties ({len(modified_properties)})\n")
    if modified_properties:
        markdown_content.append("| Property | Old Value | New Value |\n|----------|-----------|-----------|")
        for key, value in modified_properties.items():
            markdown_content.append(f"| {key} | {value['old_value']} | {value['new_value']} |")
    else:
        markdown_content.append("No modified properties.\n")

    # Folders Differences
    markdown_content.append("## Folders Differences\n")

    # Exclusions Section
    markdown_content.append(f"### Excluded Folders ({len(exclusions)})\n")
    if exclusions:
        for exclusion in exclusions:
            markdown_content.append(f"- {exclusion}")
    else:
        markdown_content.append("No exclusions applied.\n")

    # Added Folders
    markdown_content.append(f"### Added Folders ({len(added)})\n")
    if added:
        markdown_content.append("| Folder | Files |\n|--------|-------|")
        added = sorted(added, key=lambda x: x["folder_name"].lower())
        for folder in added:
            markdown_content.append(f"| {folder['folder_name']} | {folder['file_count']} |")
    else:
        markdown_content.append("No added folders.\n")

    # Removed Folders
    markdown_content.append(f"### Removed Folders ({len(removed)})\n")
    if removed:
        markdown_content.append("| Folder | Files |\n|--------|-------|")
        removed = sorted(removed, key=lambda x: x["folder_name"].lower())
        for folder in removed:
            markdown_content.append(f"| {folder['folder_name']} | {folder['file_count']} |")
    else:
        markdown_content.append("No removed folders.\n")

    # Modified Folders
    markdown_content.append(f"### Modified Folders ({len(modified)})\n")
    if modified:
        markdown_modified_files = []
        markdown_content.append("| Folder | Old Files | New Files |\n|--------|-----------|-----------|")
        modified = sorted(modified, key=lambda x: x["folder_name"].lower())
        for folder in modified:
            markdown_content.append(f"| {folder['folder_name']} | {folder['file_count_diff'][0]} | {folder['file_count_diff'][1]} |")

            # Detailed Section for Modified Files
            if folder["files_diff"]["modified"]:
                markdown_modified_files.append(f"\n#### Folder: {folder['folder_name']}\n")
                markdown_modified_files.append("| File | Old Type | New Type |\n|------|----------|----------|")
                for file_pair in folder["files_diff"]["modified"]:
                    markdown_modified_files.append(f"| {file_pair[0]['filename']} | {file_pair[0]['file_type']} | {file_pair[1]['file_type']} |")

        markdown_content.extend(markdown_modified_files)
    else:
        markdown_content.append("No modified folders.\n")

    # Write to file
    with open(output_file, 'w') as file:
        file.write("\n".join(markdown_content))

def compare_file_stats_json_files(file1: str, file2: str, exclusions: list[str],
                                  output_file: str, format: str = 'html') -> None:
    """
        Compare two file_stats JSON files and generate a report.

        :param file1: Path to the first JSON file.
        :param file2: Path to the second JSON file.
        :param exclusions: List of folder name substrings to exclude from the comparison.
        :param output_file: Path to the output file.
        :param format: Output format (default: html).
    """
    json1 = load_json(file1)
    json2 = load_json(file2)

    # Compare properties
    added_properties, removed_properties, modified_properties = compare_file_stats_sysdiag_properties(json1[0], json2[0])

    # Compare nested arrays
    added, removed, modified = compare_file_stats_folders_details(json1[1], json2[1], exclusions=exclusions)

    if format.lower() == 'html':
        # Generate HTML report
        generate_html_report(
            added_properties, removed_properties, modified_properties,
            added, removed, modified, exclusions, output_file
        )
    elif format.lower() == 'markdown':
        # Generate Markdown report
        generate_markdown_report(
            added_properties, removed_properties, modified_properties,
            added, removed, modified, exclusions, output_file
        )
    else:
        print("Unsupported format.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog='file_stats_diff',
        description='file_stats JSON files comparer'
    )
    # available for all
    parser.add_argument('file1', help='File path to the first JSON file')
    parser.add_argument('file2', help='File path to the second JSON file')
    parser.add_argument('-o', '--output', required=True, help='Output file path')
    parser.add_argument('-fmt', '--format', required=False, default='html', choices=['html', 'markdown'], help='Output format (default: html)')
    parser.add_argument('-x', '--exclude', required=False, default="system_logs.logarchive", help='Exclude specific folders, comma-separated list of substrings (default: system_logs.logarchive)')

    args = parser.parse_args()

    exclusions = args.exclude.split(",")
    compare_file_stats_json_files(args.file1, args.file2, exclusions, args.output, format=args.format)
    print(f"Report generated: {args.output}")
