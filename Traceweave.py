"""Traceweave - HTTP log analyzer.

Parses Common Log Format (CLF) log files, builds summary statistics with
pandas, and generates a text report and an hourly traffic chart.
"""

import re
import pandas as pd
import argparse
import matplotlib.pyplot as plt

TOP_HOST_COUNT = 10

LOG_PATTERN = re.compile(
    r"(\S+)"                                     # client host/IP (es. "unicomp6.unicomp.net")
    r"(?:\s+-\s+-\s+)"                           # identd/userid (ignored) -> "- -"
    r"\[([-a-zA-Z0-9:/\.\s]+)\]"                 # timestamp (es. "01/Jul/1995:00:00:06 -0400")
    r"(?:\s)"                                    # space betwin timestamp and request
    r'(?:")(\w+)(?:\s)(\S+)(?:\s)(\S+)(?:")'     # method -> "GET" , resource -> "/shuttle/countdown/", protocol -> "HTTP/1.0"
    r"(?:\s)(\d+)(?:\s)(\d+)"                    # status -> "200", bytes -> "3985"
    r"(?:\s?)"                                   # final newline 
)

class HTTPRequest():
    """Represents a single parsed HTTP request from a log line.

    Attributes:
        host (str): Client host or IP address that made the request.
        timestamp (str): Raw timestamp string as it appears in the log line.
        method (str): HTTP method (e.g. "GET", "POST").
        resource (str): Requested resource path.
        protocol (str): HTTP protocol version (e.g. "HTTP/1.0").
        status (int): HTTP response status code.
        size_bytes (int): Size of the response body in bytes.
    """

    def __init__(self, host: str, timestamp: str, method: str, resource: str, protocol: str, status: int, size_bytes: int):
        """Initializes an HTTPRequest from already-extracted log fields.

        Args:
            host (str): Client host or IP address.
            timestamp (str): Raw timestamp string.
            method (str): HTTP method.
            resource (str): Requested resource path.
            protocol (str): HTTP protocol version.
            status (int): HTTP status code (accepted as str or int, stored as int).
            size_bytes (int): Response size in bytes (accepted as str or int, stored as int).
        """
        self.host = host
        self.timestamp = timestamp
        self.method = method
        self.resource = resource
        self.protocol = protocol
        self.status = int(status)
        self.size_bytes = int(size_bytes)


class FileReader():
    """Handles reading raw log files from disk."""

    @classmethod
    def from_path(cls, path) -> list[str]:
        """Reads a log file from the given path and returns its lines.

        Args:
            path (str): Path to the log file to read.

        Returns:
            list[str]: Raw log lines, one entry per line in the file.
        """
        raw_data = []

        with open(path, "r") as file:

            for row in file:
                raw_data.append(row)

            return raw_data
    
class LogParser():
    """Parses raw log lines into structured HTTPRequest objects."""
    
    @staticmethod
    def request_collector(collector_list: list[str]):
        """Parses a list of raw log lines and aggregates the results.

        Args:
            collector_list (list[str]): Raw log lines to parse.

        Returns:
            dict[str, dict]: A dictionary with two keys:
                - 'requests' (list[HTTPRequest]): Successfully parsed requests.
                - 'metadata' (dict): Parsing statistics, with 'total_lines',
                  'parsed_lines', 'skipped_lines', and 'parsing_errors'
                  (the raw lines that failed to parse).
        """

        parsed_log = {'requests': [],
                      'metadata': {'total_lines': 0,
                                   'parsed_lines': 0,
                                   'skipped_lines': 0,
                                   'parsing_errors': []}}

        for row in collector_list:
            to_parse = LogParser.parse_line(row)
            if to_parse is not None:
                parsed_log['requests'].append(to_parse)
                parsed_log['metadata']['total_lines'] += 1
                parsed_log['metadata']['parsed_lines'] += 1
            else:
                parsed_log['metadata']['parsing_errors'].append(row)
                parsed_log['metadata']['total_lines'] += 1
                parsed_log['metadata']['skipped_lines'] += 1

        return parsed_log
    
    @staticmethod
    def parse_line(row: str) -> HTTPRequest | None :
        """Parses a single raw log line into an HTTPRequest.

        Args:
            row (str): A single raw log line.

        Returns:
            HTTPRequest | None: The parsed request, or None if the line
            does not match the expected Common Log Format pattern.
        """
        
        parsed_row = LOG_PATTERN.match(row)

        if parsed_row:
            return HTTPRequest(host=parsed_row.group(1),
                                timestamp=parsed_row.group(2),
                                method=parsed_row.group(3),
                                resource=parsed_row.group(4),
                                protocol=parsed_row.group(5),
                                status=parsed_row.group(6),
                                size_bytes=parsed_row.group(7)
                                )
        else:
            return None


class DataFrameBuilder():
    """Converts parsed log data into a pandas DataFrame."""

    @staticmethod
    def df_builder(parsed_log: dict[str, dict]) -> pd.DataFrame : 
        """Builds a DataFrame from parsed HTTPRequest objects.

        Args:
            parsed_log (dict[str, dict]): Output of
                LogParser.request_collector, containing the 'requests'
                list of HTTPRequest objects.

        Returns:
            pd.DataFrame: One row per HTTPRequest, with one column per
            HTTPRequest attribute.
        """
        requests_list = []

        for row in parsed_log['requests']:
            requests_list.append(row.__dict__)

        df = pd.DataFrame(requests_list)
        return df
    
class Analyzer():
        """Computes summary statistics and categorizations from the log DataFrame."""

        @staticmethod 
        def analyze_df(df: pd.DataFrame) -> dict[str, pd.Series]:
            """Runs the full analysis pipeline on the parsed log DataFrame.

            Adds 'status_category', 'resource_category', and
            'splitted_datetime' columns to a copy of the input DataFrame,
            then computes every summary.

            Args:
                df (pd.DataFrame): DataFrame produced by
                    DataFrameBuilder.df_builder.

            Returns:
                dict[str, pd.Series]: Summary results keyed by
                'status_summary', 'method_summary', 'host_summary',
                'resource_summary', and 'hourly_summary'.
            """
            
            analysis_result = {}

            df_edited = df.copy() 

            df_edited['status_category'] = df_edited['status'].apply(Analyzer.categorize_status)
            df_edited['resource_category'] = df_edited['resource'].apply(Analyzer.categorize_resource)
            df_edited['splitted_datetime'] = pd.to_datetime(df_edited['timestamp'], format="%d/%b/%Y:%H:%M:%S %z")
            analysis_result['status_summary'] = Analyzer.status_summary(df_edited)
            analysis_result['method_summary'] = Analyzer.method_summary(df_edited)
            analysis_result['host_summary'] = Analyzer.host_summary(df_edited)
            analysis_result['resource_summary'] = Analyzer.resource_summary(df_edited)
            analysis_result['hourly_summary'] = Analyzer.hourly_summary(df_edited)

            return analysis_result
            

        @staticmethod
        def categorize_status(status: int) -> str:
            """Maps an HTTP status code to a human-readable category.

            Args:
                status (int): HTTP status code.

            Returns:
                str: One of 'Success', 'Redirect', 'Client Error',
                'Server Error', or 'Other'.
            """

            if (status // 100) == 2:
                return 'Success'
            elif (status // 100) == 3:
                return 'Redirect'
            elif (status // 100) == 4:
                return 'Client Error'
            elif (status // 100) == 5:
                return 'Server Error'
            else:
                return 'Other'
            
        @staticmethod
        def categorize_resource(resource: str) -> str:
            """Categorizes a requested resource by its file extension.

            Args:
                resource (str): Requested resource path.

            Returns:
                str: 'Directory' if the resource ends with '/',
                'No extension' if it has no file extension, otherwise
                the lowercase extension.
            """
            if resource.endswith('/'):
                return 'Directory'
            splitted_resource = resource.lower().split('.')
            if len(splitted_resource) == 1:
                return 'No extension'
            else:
                return splitted_resource[-1]

            
        @staticmethod
        def status_summary(df_edited: pd.DataFrame) -> pd.Series:
            """Counts requests by status category.

            Args:
                df_edited (pd.DataFrame): DataFrame with a
                    'status_category' column.

            Returns:
                pd.Series: Count of requests per status category.
            """
            return df_edited['status_category'].value_counts()
        
        @staticmethod
        def method_summary(df_edited: pd.DataFrame) -> pd.Series:
            """Counts requests by HTTP method.

            Args:
                df_edited (pd.DataFrame): DataFrame with a 'method' column.

            Returns:
                pd.Series: Count of requests per HTTP method.
            """
            return df_edited['method'].value_counts()
        
        @staticmethod
        def host_summary(df_edited: pd.DataFrame) -> pd.Series:
            """Counts requests by host, keeping only the top hosts.

            Args:
                df_edited (pd.DataFrame): DataFrame with a 'host' column.

            Returns:
                pd.Series: Count of requests for the top
                TOP_HOST_COUNT hosts.
            """
            return df_edited['host'].value_counts().head(TOP_HOST_COUNT)
        
        @staticmethod
        def resource_summary(df_edited: pd.DataFrame) -> pd.Series:
            """Counts requests by resource category.

            Args:
                df_edited (pd.DataFrame): DataFrame with a
                    'resource_category' column.

            Returns:
                pd.Series: Count of requests per resource category.
            """
            return df_edited['resource_category'].value_counts()
        
        @staticmethod
        def hourly_summary(df_edited: pd.DataFrame) -> pd.Series:
            """Counts requests by hour of day.

            Args:
                df_edited (pd.DataFrame): DataFrame with a
                    'splitted_datetime' column.

            Returns:
                pd.Series: Count of requests per hour (0-23), sorted by
                hour.
            """
            hours = df_edited['splitted_datetime'].dt.hour
            return hours.value_counts().sort_index()
        
class ReportGenerator():
    """Formats and outputs analysis results as text and charts."""

    @staticmethod
    def formatted_report(analysis_dict: dict[str, pd.Series]) -> str:
        """Builds a single formatted text string from all analysis results.

        Args:
            analysis_dict (dict[str, pd.Series]): Output of
                Analyzer.analyze_df.

        Returns:
            str: Formatted report text, with one labeled section per
            summary.
        """
        string_to_return = ''
        for k, v in analysis_dict.items():
            string_to_return = string_to_return + k.capitalize().replace('_', ' ') + "\n"
            string_to_return = string_to_return + v.to_string(header=False, name=False, dtype=False) + "\n\n"
        return string_to_return
    
    @staticmethod
    def text_report(analysis_dict: dict[str, pd.Series], file_path: str) -> str:
        """Saves the formatted report to a text file.

        Args:
            analysis_dict (dict[str, pd.Series]): Output of
                Analyzer.analyze_df.
            file_path (str): Path where the report will be saved.

        Returns:
            str: Confirmation message once the file has been written.
        """
        string_to_save = ReportGenerator.formatted_report(analysis_dict)
        with open(file_path, 'w') as file:
            file.write(string_to_save)
        return 'TRACEWEAVE - report saved to file'
    
    @staticmethod
    def text_on_screen(analysis_dict: dict[str, pd.Series]) -> None:
        """Prints the formatted report to the console.

        Args:
            analysis_dict (dict[str, pd.Series]): Output of
                Analyzer.analyze_df.

        Returns:
            None
        """
        string_to_print = ReportGenerator.formatted_report(analysis_dict)
        print(string_to_print)

    @staticmethod
    def hourly_chart(hourly_summary: pd.Series, chart_path: str) -> None:
        """Generates and saves a bar chart of hourly traffic.

        Args:
            hourly_summary (pd.Series): Hourly request counts, indexed
                by hour.
            chart_path (str): Path where the chart image will be saved.

        Returns:
            None
        """
        plt.bar(x = hourly_summary.index, height = hourly_summary.values)
        plt.title('Traffic Distribution by Hour')
        plt.xlabel('Hours')
        plt.ylabel('Traffic')
        plt.savefig(chart_path)
        plt.close()


def main():
    """Parses command-line arguments and runs the full Traceweave pipeline.

    Reads the input log file, parses it, builds a DataFrame, runs the
    analysis, then writes the chart, the text report, and prints the
    report to screen.
    """

    parser = argparse.ArgumentParser(description='Traceweave - Automatic logfile Analyzer. Pass a log file to generate a full analysis report.')
    parser.add_argument('--file', help='Write your file name here', required=True)
    parser.add_argument('--export', help='Write your file name to export here, default is report.txt', default='report.txt')
    parser.add_argument('--chart', help='Write your chart name to export here, default is hourly_chart.png', default='hourly_chart.png')
    args = parser.parse_args()

    filename = args.file
    file_to_export = args.export
    chart_to_export = args.chart

    raw_string_list = FileReader.from_path(filename)
    parsed_log_list = LogParser.request_collector(raw_string_list)
    dataframe = DataFrameBuilder.df_builder(parsed_log_list)
    analysis = Analyzer.analyze_df(dataframe)
    
    ReportGenerator.hourly_chart(analysis['hourly_summary'], chart_to_export)
    ReportGenerator.text_report(analysis, file_to_export)
    ReportGenerator.text_on_screen(analysis)

if __name__ == "__main__":
    main()