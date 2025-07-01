#! /usr/bin/env python3

import importlib
import os
import magic
from sysdiagnose.utils.base import BaseAnalyserInterface, BaseParserInterface, SysdiagnoseConfig, logger
from sysdiagnose.parsers.remotectl_dumpstate import RemotectlDumpstateParser


class CoverageAnalyser(BaseAnalyserInterface):
    description = "Provides parser coverage information"
    format = "html"

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
        super().__init__(__file__, config, case_id)

    def execute(self):
        result = []
        rctl_parser = RemotectlDumpstateParser(self.config, self.case_id)
        rctl_result = rctl_parser.get_result()
        # device info
        device_info = {}
        try:
            device_info = {
                "os_version": rctl_result['Local device']['Properties']['OSVersion'],
                "build": rctl_result['Local device']['Properties']['BuildVersion'],
                "product_name": rctl_result['Local device']['Properties']['ProductName'],
                "product_type": rctl_result['Local device']['Properties']['ProductType']
            }
        except KeyError:
            logger.exception("Issue extracting device info")
        result.append(device_info)

        # Calculate parser coverage
        result.append(self.get_parser_coverage(self.case_data_subfolder))

        # return result
        return self.generate_html_report(result[0], result[1])

    def get_parser_coverage(self, path: str) -> dict:
        """
        Get the parser coverage for a given path.
        :param path: The path to the file or directory.
        :return: A dictionary containing the parser coverage information.
        """
        # get all files and folders
        coverage = {}
        for root, dirs, files in os.walk(path):
            for file in files:
                # skip files that start with a .
                if os.path.basename(file).startswith('.'):
                    continue

                coverage[os.path.join(root, file)] = {
                    'file_type': self.get_file_type(os.path.join(root, file)),
                    'folder_name': os.path.relpath(root, start=path),
                    'parser': None,
                    'parser_format': None
                }

        for parser_name in self.config.get_parsers():
            parser = self.get_parser(parser_name)
            if parser:
                for file in parser.get_log_files():
                    if file in coverage:
                        coverage[file]['parser'] = parser_name
                        coverage[file]['parser_format'] = parser.format
                    # We are assuming the parser always returns files, not just folders
                    elif not os.path.isdir(file):
                        coverage[file] = {
                            'file_type': 'unknown',
                            'folder_name': os.path.relpath(file, start=path),
                            'parser': parser_name,
                            'parser_format': parser.format
                        }

        return coverage

    def get_parser(self, parser_name: str) -> BaseParserInterface:
        """
        Get the parser instance for a given parser name.
        :param parser_name: The name of the parser.
        :return: An instance of the parser class.
        """
        module = importlib.import_module(f'sysdiagnose.parsers.{parser_name}')
        # figure out the class name
        obj = None
        obj_instance = None
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, BaseParserInterface) and obj is not BaseParserInterface:
                obj_instance: BaseParserInterface = obj(config=self.config, case_id=self.case_id)

                return obj_instance
        return None

    def get_file_type(self, file_path: str) -> str:
        """
        Get the file type using the python-magic library.
        :param file_path: The path to the file.
        :return: The file type as a string.
        """
        return magic.from_file(file_path, mime=True)

    def generate_html_report(self, device_info: dict, coverage: dict) -> str:
        """
        Generate an HTML report with four sections:
        1. Device Information (a table with device details).
        2. Statistics (includes Coverage Overview and Parser Overview subsections).
        3. Parsers Information (a table with parser details).
        4. Details (a collapsible section with a table of coverage data).
        """
        import pandas as pd
        import matplotlib.pyplot as plt
        import base64
        from io import BytesIO
        from jinja2 import Template

        # Convert coverage dictionary to a Pandas DataFrame
        coverage_df = pd.DataFrame.from_dict(coverage, orient='index')

        # Calculate statistics for parsed vs. not parsed files
        parsed_count = coverage_df['parser'].notna().sum()
        not_parsed_count = coverage_df['parser'].isna().sum()

        # Generate a pie chart for parsed vs. not parsed files
        labels = ['Parsed Files', 'Not Parsed Files']
        sizes = [parsed_count, not_parsed_count]
        colours = ['#4caf50', '#f44336']
        explode = (0.1, 0)  # Slightly "explode" the first slice (Parsed Files)

        plt.figure(figsize=(6, 6))
        plt.pie(sizes, labels=labels, colors=colours, autopct='%1.1f%%', startangle=140, explode=explode)
        plt.title('Coverage')

        # Save the pie chart to a base64-encoded string
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        parsed_chart_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close()

        # Generate data for the tables
        folder_counts = coverage_df[coverage_df['parser'].isna()]['folder_name'].value_counts()

        # Data for the least parsed folders (folders with the fewest files having parser=None)
        least_parsed_folders = folder_counts.nsmallest(10).reset_index()
        least_parsed_folders.columns = ['Folder', 'Count']

        # Data for the top folders with the most files having parser=None
        top_folders_with_no_parser = folder_counts.nlargest(10).reset_index()
        top_folders_with_no_parser.columns = ['Folder', 'Count']

        # Calculate statistics for parser coverage ratio
        parser_counts = coverage_df['parser'].value_counts()
        parser_counts['Not Parsed'] = not_parsed_count  # Add non-parsed files as a separate category

        # Generate a histogram for parser coverage ratio with a logarithmic y-axis
        plt.figure(figsize=(10, 6))
        parser_counts.sort_values(ascending=False).plot(
            kind='bar',
            color=['#f44336' if parser == 'Not Parsed' else '#4caf50' for parser in parser_counts.index]
        )
        plt.title('Parser Coverage Ratio')
        plt.xlabel('Parser')
        plt.ylabel('File Count (Log Scale)')
        plt.yscale('log')  # Set y-axis to logarithmic scale
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # Save the histogram to a base64-encoded string
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        histogram_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close()

        # Calculate distinct parser statistics
        distinct_parsers_df = coverage_df.drop_duplicates(subset=['parser'])
        total_parsers = distinct_parsers_df['parser'].notna().sum()

        # Calculate distinct parser format statistics
        parser_format_counts = distinct_parsers_df['parser_format'].value_counts()

        # Generate a pie chart for parser formats
        plt.figure(figsize=(6, 6))
        parser_format_counts.plot(
            kind='pie',
            autopct='%1.1f%%',
            startangle=140,
            colors=plt.cm.tab20.colors[:len(parser_format_counts)],
            legend=False
        )
        plt.title('Parsers by Format')

        # Save the parser format pie chart to a base64-encoded string
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        parser_format_chart_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close()

        # Generate Parsers Information Table
        parsers_info = []
        for parser_name, group in coverage_df.groupby('parser'):
            if parser_name is not None:
                # Total files parsed by this parser
                total_files_parsed = len(group)
                # Files with a known file_type (not 'unknown')
                known_file_type_count = len(group[group['file_type'] != 'unknown'])
                # Calculate coverage as a percentage
                coverage = round((known_file_type_count / total_files_parsed) * 100) if total_files_parsed > 0 else 0
                parsers_info.append({
                    'parser_name': parser_name,
                    'format': group['parser_format'].iloc[0],
                    'coverage': f"{coverage}%"  # Format as a percentage
                })

        # Convert DataFrame to HTML table for the Details section
        coverage_table_html = coverage_df.to_html(
            classes='coverage-table',
            border=0,
            index=True,
            index_names=False,
            justify='left',
            escape=False
        )

        # Jinja2 template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Coverage Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1, h2, h3 { color: #333; }
                .charts-row { display: flex; justify-content: space-around; align-items: center; margin-top: 20px; }
                .chart-container { flex: 1; padding: 10px; }
                .chart-container img { max-width: 100%; height: auto; display: block; margin: 0 auto; }
                .big-number { font-size: 48px; font-weight: bold; text-align: center; margin: 20px 0; }
                .collapsible { cursor: pointer; padding: 10px; border: none; text-align: left; outline: none; font-size: 16px; font-weight: bold; }
                .collapsible.active, .collapsible:hover { background-color: #f1f1f1; }
                .content { display: none; padding: 10px; border: 1px solid #ddd; margin-top: 5px; border-radius: 8px; }
                .content.show { display: block; }
                table { border-collapse: collapse; width: 100%; margin-top: 10px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f4f4f4; }
                .section { margin-bottom: 20px; }
                .light-red { background-color: #ffe6e6; }
            </style>
            <script>
                function toggleContent(id) {
                    var content = document.getElementById(id);
                    if (content.classList.contains("show")) {
                        content.classList.remove("show");
                    } else {
                        content.classList.add("show");
                    }
                }
            </script>
        </head>
        <body>
            <h1>Coverage Report</h1>

            <!-- Device Information Section -->
            <div class="section">
                <h2>Device Information</h2>
                <table>
                    <tr>
                        <th>Property</th>
                        <th>Value</th>
                    </tr>
                    {% for key, value in device_info.items() %}
                    <tr>
                        <td>{{ key }}</td>
                        <td>{{ value }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>

            <!-- Statistics Section -->
            <div class="section">
                <h2>Statistics</h2>

                <!-- Coverage Overview -->
                <h3>Coverage Overview</h3>
                <div class="charts-row">
                    <div class="chart-container">
                        <h4>Coverage</h4>
                        <img src="data:image/png;base64,{{ parsed_chart_base64 }}" alt="Coverage">
                    </div>
                    <div class="chart-container">
                        <h4>Parser Coverage Ratio</h4>
                        <img src="data:image/png;base64,{{ histogram_base64 }}" alt="Parser Coverage Ratio">
                    </div>
                </div>
                <div class="charts-row">
                    <div class="chart-container">
                        <h4>Folders with Least Parsed Files</h4>
                        <table>
                            <tr>
                                <th>Folder</th>
                                <th>Count</th>
                            </tr>
                            {% for row in least_parsed_folders %}
                            <tr>
                                <td>{{ row.Folder }}</td>
                                <td>{{ row.Count }}</td>
                            </tr>
                            {% endfor %}
                        </table>
                    </div>
                    <div class="chart-container">
                        <h4>Top Folders with Files Having No Parser</h4>
                        <table>
                            <tr>
                                <th>Folder</th>
                                <th>Count</th>
                            </tr>
                            {% for row in top_folders_with_no_parser %}
                            <tr>
                                <td>{{ row.Folder }}</td>
                                <td>{{ row.Count }}</td>
                            </tr>
                            {% endfor %}
                        </table>
                    </div>
                </div>
                <!-- Parser Overview -->
                <h3>Parser Overview</h3>
                <div class="charts-row">
                    <div class="chart-container">
                        <div class="big-number">{{ total_parsers }}</div>
                        <p style="text-align: center;">Total Parsers</p>
                    </div>
                    <div class="chart-container">
                        <h4>Parsers by Format</h4>
                        <img src="data:image/png;base64,{{ parser_format_chart_base64 }}" alt="Parsers by Format">
                    </div>
                </div>
            </div>
            <!-- Parsers Information -->
            <div class="section">
                <h2 class="collapsible" onclick="toggleContent('parsers-info-section')">Parsers Information</h2>
                <div id="parsers-info-section" class="content">
                    <table>
                        <tr>
                            <th>Parser Name</th>
                            <th>Format</th>
                            <th>Coverage</th>
                        </tr>
                        {% for parser in parsers_info %}
                        <tr style="background-color: {{ get_coverage_color(parser.coverage) }};">
                            <td>{{ parser.parser_name }}</td>
                            <td>{{ parser.format }}</td>
                            <td>{{ parser.coverage }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>
            </div>
            <!-- Details Section -->
            <div class="section">
                <h2 class="collapsible" onclick="toggleContent('details-section')">Details</h2>
                <div id="details-section" class="content">
                    {{ coverage_table_html | safe }}
                </div>
            </div>
        </body>
        </html>
        """

        # Render the template with Jinja2
        template = Template(html_template)
        rendered_html = template.render(
            device_info=device_info,
            parsed_chart_base64=parsed_chart_base64,
            histogram_base64=histogram_base64,
            least_parsed_folders=least_parsed_folders.to_dict(orient='records'),
            top_folders_with_no_parser=top_folders_with_no_parser.to_dict(orient='records'),
            parser_format_chart_base64=parser_format_chart_base64,
            total_parsers=total_parsers,
            parsers_info=parsers_info,
            coverage_table_html=coverage_table_html,
            get_coverage_color=get_coverage_color  # Pass the function to the template
        )
        return rendered_html


def get_coverage_color(coverage: str) -> str:
    """
    Returns a colour based on the coverage percentage.
    :param coverage: Coverage percentage as a string (e.g., "85.00%").
    :return: A CSS colour string.
    """
    # Convert coverage to a float
    coverage_value = float(coverage.strip('%'))

    # Define colour ranges
    if 80 <= coverage_value <= 100:
        # Green to Green-Yellow
        green = int(255 - (coverage_value - 80) * (255 - 173) / 20)  # Linear interpolation
        return f"rgb(173, 255, {green})"
    elif 50 < coverage_value < 80:
        # Green-Yellow to Yellow
        red = int(173 + (coverage_value - 50) * (255 - 173) / 30)
        return f"rgb({red}, 255, 0)"
    elif 30 < coverage_value <= 50:
        # Yellow to Yellow-Orange
        green = int(255 - (coverage_value - 30) * (255 - 165) / 20)
        return f"rgb(255, {green}, 0)"
    else:
        # Yellow-Orange to Red
        red = int(255 - (coverage_value) * (255 - 165) / 30)
        return f"rgb({red}, 0, 0)"
