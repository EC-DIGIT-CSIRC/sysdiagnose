import json
from typing import Generator

from sysdiagnose.utils.base import BaseAnalyserInterface, logger
from sysdiagnose.parsers.plists import PlistParser


class PListAnalyzer(BaseAnalyserInterface):
    """
    Analyzer that gathers and processes information from plist files,
    converting relevant entries into a structured JSONL format for further analysis.
    """

    description = 'Gathers information from a plist file.'
    format = 'jsonl'

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)
        self.parser = PlistParser(config, case_id)

    def execute(self) -> Generator[dict, None, None]:
        """
        Executes all available extraction methods dynamically.

        This method identifies and executes all internal methods within this class whose names
        begin with '__extract_plist'. Each identified method is expected to yield dictionary-formatted
        results, facilitating modular and extensible parsing logic.

        :yield: Dictionaries containing extracted plist details from various sources.
        """
        self.parser.save_result()

        for func in dir(self):
            if func.startswith(f'_{self.__class__.__name__}__extract_plist'):
                yield from getattr(self, func)()

    def __extract_plist_mdm_data(self) -> Generator[dict, None, None]:
        """
        Extracts MDM profile information from a dedicated plist JSON file.

        This method specifically targets the 'logs_MCState_Shared_MDM.plist.json' file, parsing each entry to
        extract key attributes related to device profiles.

        Each extracted entry is yielded as a dictionary, along with the original source filename for traceability.

        :yield: A dictionary containing extracted MDM details.
        """
        entity_type: str = 'logs_MCState_Shared_MDM.plist.json'
        file_path: str = f'{self.parser.output_folder}/{entity_type}'

        try:
            with open(file_path, 'r') as f:
                for line in f:
                    entry = json.loads(line)

                    mdm_entry: dict[str, str] = {
                        'ManagingProfileIdentifier': entry.get('ManagingProfileIdentifier'),
                        'AccessRights': entry.get('AccessRights'),
                        'LastPollingAttempt': entry.get('LastPollingAttempt'),
                        'source': entity_type,
                    }

                    yield mdm_entry

        except FileNotFoundError as e:
            logger.warning(f'{entity_type} not found for {self.case_id}. {e}')
        except Exception as e:
            logger.exception(f'ERROR while extracting {entity_type} file. {e}')
