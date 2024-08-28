import glob
import os
from utils.base import BaseParserInterface


class CrashLogsParser(BaseParserInterface):
    '''
    # FIXME Have a look at the interesting evidence first, see which files are there that are not on other devices
    - crashes_and_spins folder
    - ExcUserFault file
    - crashes_and_spins/Panics subfolder
    - summaries/crashes_and_spins.log

    Though one as there is not necessary a fixed structure
    - first line is json
    - rest depends ...

    Or perhaps include that in a normal log-parser.
    And do the secret magic in the hunting rule
    '''

    description = "Parsing crashes folder"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_log_files(self) -> list:
        log_files_globs = [
            'crashes_and_spins/*.ips'
        ]
        log_files = []
        for log_files_glob in log_files_globs:
            log_files.extend(glob.glob(os.path.join(self.case_data_subfolder, log_files_glob)))

        return log_files

    def execute(self) -> list | dict:
        files = self.get_log_files()
        raise NotImplementedError("not implemented yet")
        for file in files:
            print(f"Processing file: {file}")

    def parse_file(path: str) -> list | dict:
        print(f"Parsing file: {path}")
