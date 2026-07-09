import os 

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





def main(): #implementiamo argparse in un secondo momento, per i test procediamo senza argparse impostando momentaneamente un dataframe fisso
    path = 'C:/Users/bocca/Desktop/boccassinisergio-afk/new/prova.txt'
    analyzer = FileReader.from_path(path)
    collector = FileReader.request_collector(analyzer)

    print(analyzer)


main() #sostituire prima del rilascio con if __name__ == "__main__": main()