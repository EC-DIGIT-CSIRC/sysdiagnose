import argparse
import json
from jinja2 import Template
import pandas as pd


def load_json(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def compare_sysdiag_properties(obj1: dict, obj2: dict) -> tuple[dict, dict, dict]:
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

def compare_coverage_details(obj1: dict, obj2: dict) -> list[dict]:
    """
    Compare the coverage details of two dictionaries and return the comparison as a list of dictionaries.

    :param obj1: First dictionary (coverage details from the first JSON file).
    :param obj2: Second dictionary (coverage details from the second JSON file).
    :return: A list of dictionaries containing the comparison data.
    """

    def calculate_coverage(data: dict) -> pd.DataFrame:
        """
        Calculate the coverage for each parser.

        :param data: Dictionary containing file details.
        :return: A DataFrame with parser names as the index and coverage details as columns.
        """
        df = pd.DataFrame.from_dict(data, orient='index')

        # Assign "no-parser" to files without a parser
        df['parser'] = df['parser'].fillna('no-parser')

        # Calculate the total number of files
        total_files = len(df)

        # Group by parser and calculate coverage
        def calculate_group_coverage(group):
            parsed_files = (group['file_type'] != 'unknown').sum()
            total_group_files = len(group)
            # For "no-parser", divide by the total number of files
            if group.name == 'no-parser':
                coverage = parsed_files / total_files if total_files > 0 else 0
            else:
                coverage = parsed_files / total_group_files if total_group_files > 0 else 0
            return {
                'parsed_files': parsed_files,
                'total_files': total_group_files,
                'coverage': coverage
            }

        coverage = df.groupby('parser').apply(calculate_group_coverage,
                                              # Deprecation warning:
                                              # https://stackoverflow.com/questions/77969964/deprecation-warning-with-groupby-apply
                                              include_groups=False)

        return pd.DataFrame(coverage.tolist(), index=coverage.index)

    # Calculate coverage for both objects
    coverage1 = calculate_coverage(obj1)
    coverage2 = calculate_coverage(obj2)

    # Merge the two coverage DataFrames for comparison
    comparison = pd.merge(
        coverage1, coverage2,
        how='outer',
        left_index=True,
        right_index=True,
        suffixes=('_old', '_new')
    ).fillna(0)  # Fill NaN values with 0 for parsers missing in one of the objects

    # Convert the comparison DataFrame to a list of dictionaries
    return comparison.reset_index().to_dict(orient='records')

def generate_html_report(comparison_data: list[dict], added_properties: dict, removed_properties: dict,
                         modified_properties: dict, output_file: str) -> None:
    """
    Generate an HTML report for parser coverage comparison and sysdiag properties using Jinja2.

    :param comparison_data: List of dictionaries containing parser coverage comparison data.
    :param added_properties: Dictionary of added properties.
    :param removed_properties: Dictionary of removed properties.
    :param modified_properties: Dictionary of modified properties.
    :param output_file: Output HTML file path.
    """
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Parser Coverage and Sysdiag Properties Comparison</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            .added { background-color: #d4f8d4; border: 1px solid #a3e6a3; padding: 10px; margin-bottom: 10px; border-radius: 8px; }
            .removed { background-color: #f8d4d4; border: 1px solid #e6a3a3; padding: 10px; margin-bottom: 10px; border-radius: 8px; }
            .modified { background-color: #f8f4d4; border: 1px solid #e6e3a3; padding: 10px; margin-bottom: 10px; border-radius: 8px; }
            .collapsible { cursor: pointer; padding: 10px; border: none; text-align: left; outline: none; font-size: 16px; font-weight: bold; }
            .collapsible.added { color: #2e7d32; } /* Dark green for added */
            .collapsible.removed { color: #c62828; } /* Dark red for removed */
            .collapsible.modified { color: #f9a825; } /* Dark yellow for modified */
            .content { display: none; padding: 10px; border: 1px solid #ccc; margin-top: 5px; border-radius: 8px; }
            table { border-collapse: collapse; width: 100%; margin-top: 10px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f4f4f4; color: #333; font-weight: bold; }
            th.added { background-color: #2e7d32; color: white; } /* Dark green for added table headers */
            th.removed { background-color: #c62828; color: white; } /* Dark red for removed table headers */
            th.modified { background-color: #f9a825; color: black; } /* Dark yellow for modified table headers */
            .coverage-green { background-color: #d4f8d4; } /* Light green for 100% coverage */
            .coverage-red { background-color: #f8d4d4; } /* Light red for 0% coverage */
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
        </script>
    </head>
    <body>
        <h1>Parser Coverage and Sysdiag Properties Comparison</h1>

        <!-- Sysdiag Properties Comparison -->
        <h2>Sysdiag Properties Comparison</h2>

        <!-- Added Properties Section -->
        <div class="added">
            <h2 class="collapsible added" onclick="toggleContent('added-properties')">Added Properties ({{ added_properties|length }})</h2>
            <div id="added-properties" class="content">
                {% if added_properties %}
                <table>
                    <tr>
                        <th class="added">Property</th>
                        <th class="added">Value</th>
                    </tr>
                    {% for key, value in added_properties.items() %}
                    <tr>
                        <td>{{ key }}</td>
                        <td>{{ value }}</td>
                    </tr>
                    {% endfor %}
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
                        <th class="removed">Property</th>
                        <th class="removed">Value</th>
                    </tr>
                    {% for key, value in removed_properties.items() %}
                    <tr>
                        <td>{{ key }}</td>
                        <td>{{ value }}</td>
                    </tr>
                    {% endfor %}
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

        <!-- Parser Coverage Comparison -->
        <h2>Parser Coverage Comparison</h2>
        <table>
            <tr>
                <th>Parser Name</th>
                <th>Coverage (Old)</th>
                <th>Coverage (New)</th>
            </tr>
            {% for row in comparison_data %}
            <tr>
                <td>{{ row.parser }}</td>
                <td class="{{ 'coverage-green' if row.coverage_old == 1 else 'coverage-red' if row.coverage_old == 0 else '' }}">
                    {{ (row.coverage_old * 100) | round }}%
                </td>
                <td class="{{ 'coverage-green' if row.coverage_new == 1 else 'coverage-red' if row.coverage_new == 0 else '' }}">
                    {{ (row.coverage_new * 100) | round }}%
                </td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    template = Template(html_template)
    rendered_html = template.render(
        comparison_data=comparison_data,
        added_properties=added_properties,
        removed_properties=removed_properties,
        modified_properties=modified_properties
    )

    with open(output_file, 'w') as file:
        file.write(rendered_html)

def generate_markdown_report(comparison_data: list[dict], added_properties: dict, removed_properties: dict,
                             modified_properties: dict, output_file: str) -> None:
    """
    Generate a Markdown report for parser coverage comparison and sysdiag properties.

    :param comparison_data: List of dictionaries containing parser coverage comparison data.
    :param added_properties: Dictionary of added properties.
    :param removed_properties: Dictionary of removed properties.
    :param modified_properties: Dictionary of modified properties.
    :param output_file: Output Markdown file path.
    """
    with open(output_file, 'w') as file:
        # Title
        file.write("# Parser Coverage and Sysdiag Properties Comparison\n\n")

        # Sysdiag Properties Comparison
        file.write("## Sysdiag Properties Comparison\n\n")

        # Added Properties
        file.write("### Added Properties\n")
        if added_properties:
            file.write("| Property | Value |\n")
            file.write("|----------|-------|\n")
            for key, value in added_properties.items():
                file.write(f"| {key} | {value} |\n")
        else:
            file.write("No added properties.\n")
        file.write("\n")

        # Removed Properties
        file.write("### Removed Properties\n")
        if removed_properties:
            file.write("| Property | Value |\n")
            file.write("|----------|-------|\n")
            for key, value in removed_properties.items():
                file.write(f"| {key} | {value} |\n")
        else:
            file.write("No removed properties.\n")
        file.write("\n")

        # Modified Properties
        file.write("### Modified Properties\n")
        if modified_properties:
            file.write("| Property | Old Value | New Value |\n")
            file.write("|----------|-----------|-----------|\n")
            for key, value in modified_properties.items():
                file.write(f"| {key} | {value['old_value']} | {value['new_value']} |\n")
        else:
            file.write("No modified properties.\n")
        file.write("\n")

        # Parser Coverage Comparison
        file.write("## Parser Coverage Comparison\n\n")
        if comparison_data:
            file.write("| Parser Name | Coverage (Old) | Coverage (New) |\n")
            file.write("|-------------|----------------|----------------|\n")
            for row in comparison_data:
                coverage_old = f"{round(row['coverage_old'] * 100)}%"
                coverage_new = f"{round(row['coverage_new'] * 100)}%"
                file.write(f"| {row['parser']} | {coverage_old} | {coverage_new} |\n")
        else:
            file.write("No parser coverage data available.\n")
        file.write("\n")

    print(f"Markdown report generated: {output_file}")

def compare_coverage_json_files(file1: str, file2: str,
                                output_file: str, format: str = 'html') -> None:
    """
        Compare two file_stats JSON files and generate a report.

        :param file1: Path to the first JSON file.
        :param file2: Path to the second JSON file.
        :param output_file: Path to the output file.
        :param format: Output format (default: html).
    """
    json1 = load_json(file1)
    json2 = load_json(file2)

    # Compare properties
    added_properties, removed_properties, modified_properties = compare_sysdiag_properties(json1[0], json2[0])

    # Compare nested arrays
    comparison_data = compare_coverage_details(json1[1], json2[1])

    if format.lower() == 'html':
        # Generate HTML report
        generate_html_report(
            comparison_data, added_properties, removed_properties, modified_properties, output_file
        )
    elif format.lower() == 'markdown':
        # Generate Markdown report
        generate_markdown_report(
            comparison_data, added_properties, removed_properties, modified_properties, output_file
        )


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

    args = parser.parse_args()

    compare_coverage_json_files(args.file1, args.file2, args.output, format=args.format)
    print(f"Report generated: {args.output}")
