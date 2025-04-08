#! /usr/bin/env python3

import importlib
import os
import pandas as pd

from jinja2 import Template
import magic
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from sysdiagnose.utils.base import BaseAnalyserInterface, BaseParserInterface, logger


class CoverageAnalyser(BaseAnalyserInterface):
    description = "Provides parser coverage information"
    format = "html"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def execute(self):
        # get all files and folders
        coverage = {}
        for root, dirs, files in os.walk(self.case_data_folder):
            for file in files:
                # skip files that start with a .
                if os.path.basename(file).startswith('.'):
                    continue

                coverage[os.path.join(root, file)] = {
                    'file_type': self.get_file_type(os.path.join(root, file)),
                    'folder_name': os.path.relpath(root, start=self.case_data_folder),
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
                            'folder_name': os.path.relpath(file, start=self.case_data_folder),
                            'parser': parser_name,
                            'parser_format': parser.format
                        }

        # return coverage
        return self.generate_html_report(coverage)

    def get_parser(self, parser_name: str) -> BaseParserInterface:
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
        return magic.from_file(file_path, mime=True)

    def generate_html_report(self, coverage: dict) -> str:
        """
        Generate an HTML report with three sections:
        1. Statistics (includes Coverage Overview and Parser Overview subsections).
        2. Details (a collapsible section with a table of coverage data).
        """
        # Convert coverage dictionary to a Pandas DataFrame
        coverage_df = pd.DataFrame.from_dict(coverage, orient='index')

        # Calculate statistics for parsed vs. not parsed files
        parsed_count = coverage_df['parser'].notna().sum()
        not_parsed_count = coverage_df['parser'].isna().sum()

        # Generate a pie chart for parsed vs. not parsed files
        labels = ['Parsed Files', 'Not Parsed Files']
        sizes = [parsed_count, not_parsed_count]
        colors = ['#4caf50', '#f44336']
        explode = (0.1, 0)  # Slightly "explode" the first slice (Parsed Files)

        plt.figure(figsize=(6, 6))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140, explode=explode)
        plt.title('Coverage')

        # Save the pie chart to a base64-encoded string
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        parsed_chart_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close()

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
        plt.tight_layout()  # Adjust layout to prevent cutting off labels

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
                missing_files = group[group['file_type'] == 'unknown'].index.tolist()
                parsers_info.append({
                    'parser_name': parser_name,
                    'format': group['parser_format'].iloc[0],
                    'missing_files': ', '.join(missing_files) if missing_files else 'None'
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

                <!-- Parsers Information -->
                <div class="section">
                    <h3 class="collapsible" onclick="toggleContent('parsers-info-section')">Parsers Information</h3>
                    <div id="parsers-info-section" class="content">
                        <table>
                            <tr>
                                <th>Parser Name</th>
                                <th>Format</th>
                                <th>Missing Files</th>
                            </tr>
                            {% for parser in parsers_info %}
                            <tr class="{% if parser.missing_files != 'None' %}light-red{% endif %}">
                                <td>{{ parser.parser_name }}</td>
                                <td>{{ parser.format }}</td>
                                <td>{{ parser.missing_files }}</td>
                            </tr>
                            {% endfor %}
                        </table>
                    </div>
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
            parsed_chart_base64=parsed_chart_base64,
            histogram_base64=histogram_base64,
            parser_format_chart_base64=parser_format_chart_base64,
            total_parsers=total_parsers,
            parsers_info=parsers_info,
            coverage_table_html=coverage_table_html
        )
        return rendered_html
