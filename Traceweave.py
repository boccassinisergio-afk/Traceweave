import re
import pandas as pd
import argparse

TOP_HOST_COUNT = 10

LOG_PATTERN = re.compile(
    r"(\S+)"                                     # host -------> scrivi esempi per ogni parsing
    r"(?:\s+-\s+-\s+)"                           # identd/userid (scartati) --------> indichiamolo nel readme, con esempi pratici per evitare che sia arte oscura
    r"\[([-a-zA-Z0-9:/\.\s]+)\]"                 # timestamp 
    r"(?:\s)"                                    # spazio
    r'(?:")(\w+)(?:\s)(\S+)(?:\s)(\S+)(?:")'     # method, resource, protocol 
    r"(?:\s)(\d+)(?:\s)(\d+)"                    # status, bytes 
    r"(?:\s?)"                                   # newline finale (scartato)
)

class HTTPRequest(): 
    def __init__(self, host: str, timestamp: str, method: str, resource: str, protocol: str, status: int, size_bytes: int):
        self.host = host
        self.timestamp = timestamp
        self.method = method
        self.resource = resource
        self.protocol = protocol
        self.status = int(status)
        self.size_bytes = int(size_bytes)


class FileReader():

    @classmethod
    def from_path(cls, path):
        raw_data = []

        with open(path, "r") as file:

            for row in file:
                raw_data.append(row)

            return raw_data
    
class LogParser():
    
    @staticmethod
    def request_collector(collector_list: list[str]):

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

    @staticmethod
    def DFBuilder(parsed_log: dict[str, dict]) -> pd.DataFrame : 
        requests_list = []

        for row in parsed_log['requests']:
            requests_list.append(row.__dict__)

        df = pd.DataFrame(requests_list)
        return df
    
class Analyzer():
        
        @staticmethod 
        def analyze_df(df: pd.DataFrame) -> dict[str, pd.Series]: #si occupa di inserire i vari sommari ricevuti, in un dict AnalysisResult da inviare al generatore report
            
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
            if resource.endswith('/'):
                return 'Directory'
            splitted_resource = resource.lower().split('.')
            if len(splitted_resource) == 1:
                return 'No extension'
            else:
                return splitted_resource[-1]

            
        @staticmethod
        def status_summary(df_edited: pd.DataFrame) -> pd.Series:
            return df_edited['status_category'].value_counts()
        
        @staticmethod
        def method_summary(df_edited: pd.DataFrame) -> pd.Series:
            return df_edited['method'].value_counts()
        
        @staticmethod
        def host_summary(df_edited: pd.DataFrame) -> pd.Series:
            return df_edited['host'].value_counts().head(TOP_HOST_COUNT)
        
        @staticmethod
        def resource_summary(df_edited: pd.DataFrame) -> pd.Series:
            return df_edited['resource_category'].value_counts()
        
        @staticmethod
        def hourly_summary(df_edited: pd.DataFrame) -> pd.Series:
            hours = df_edited['splitted_datetime'].dt.hour
            return hours.value_counts().sort_index()
        
class ReportGenerator():

    @staticmethod
    def formatted_report(analysis_dict: dict[str, pd.Series]) -> str:
        string_to_return = ''
        for k, v in analysis_dict.items():
            string_to_return = string_to_return + k.capitalize().replace('_', ' ') + "\n"
            string_to_return = string_to_return + v.to_string(dtype=False) + "\n\n"
        return string_to_return


def main():

    parser = argparse.ArgumentParser(description='Traceweave - Automatic logfile Analyzer. Pass a log file to generate a full analysis report.')
    parser.add_argument('--file', help='Write your file name here', required=True)
    args = parser.parse_args()

    filename = args.file
    raw_string_list = FileReader.from_path(filename)
    parsed_log_list = LogParser.request_collector(raw_string_list)
    dataframe = DataFrameBuilder.DFBuilder(parsed_log_list)
    analysis = Analyzer.analyze_df(dataframe)

main() #sostituire prima del rilascio con if __name__ == "__main__": main()