from datetime import datetime
import glob
import json
import os
from typing import Generator

from sysdiagnose.utils.base import BaseAnalyserInterface, SysdiagnoseConfig, logger, Event
from sysdiagnose.parsers.plists import PlistParser


class PListAnalyzer(BaseAnalyserInterface):
    """
    Analyzer that gathers and processes information from plist files,
    converting relevant entries into a structured JSONL format for further analysis.
    """

    description = 'Gathers information from a plist file.'
    format = 'jsonl'

    def __init__(self, config: SysdiagnoseConfig, case_id: str):
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

    def _build_profile_hash_map(self) -> dict:
        """
        Builds a mapping from profile identifiers to their SHA-256 stub file hashes.

        Scans all profile-*.stub.json files in the parser output folder, extracts the
        PayloadIdentifier and PayloadUUID from each, and maps them to the SHA-256 hash
        embedded in the stub filename.

        Returns a dict with two key formats per profile:
          - PayloadIdentifier -> hash (e.g. 'com.apple.basebandlogging' -> '4c14f9f4...')
          - PayloadIdentifier-PayloadUUID -> hash (e.g. 'com.apple.basebandlogging-39C9D78D-...' -> '4c14f9f4...')
        """
        hash_map = {}
        stub_pattern = os.path.join(self.parser.output_folder, 'logs_MCState_Shared_profile-*.stub.json')

        for stub_path in glob.glob(stub_pattern):
            filename = os.path.basename(stub_path)
            # Extract hash from filename: logs_MCState_Shared_profile-{hash}.stub.json
            prefix = 'logs_MCState_Shared_profile-'
            suffix = '.stub.json'
            if not filename.startswith(prefix) or not filename.endswith(suffix):
                continue
            stub_hash = filename[len(prefix):-len(suffix)]

            try:
                with open(stub_path, 'r') as f:
                    stub_data = json.loads(f.read())

                payload_id = stub_data.get('PayloadIdentifier')
                payload_uuid = stub_data.get('PayloadUUID')

                if payload_id:
                    hash_map[payload_id] = stub_hash
                if payload_id and payload_uuid:
                    hash_map[f'{payload_id}-{payload_uuid}'] = stub_hash
            except Exception as e:
                logger.warning(f'Could not parse profile stub {filename}: {e}')

        return hash_map

    def __extract_plist_mdm_data(self) -> Generator[dict, None, None]:
        """
        Extracts MDM profile information from a dedicated plist JSON file.

        This method specifically targets the 'logs_MCState_Shared_MDM.plist.json' file, parsing each entry to
        extract key attributes related to device profiles including server URLs, capabilities,
        and authentication details.

        Each extracted entry is yielded as a dictionary, along with the original source filename for traceability.

        :yield: A dictionary containing extracted MDM details.
        """
        entity_type: str = 'logs_MCState_Shared_MDM.plist.json'
        file_path: str = f'{self.parser.output_folder}/{entity_type}'

        # Fields to extract into the data dict for forensic enrichment
        mdm_fields = [
            'AccessRights',
            'ManagingProfileIdentifier',
            'ServerURL',
            'CheckInURL',
            'CheckOutWhenRemoved',
            'Topic',
            'IdentityCertificateUUID',
            'SignMessage',
            'UDID',
            'ServerCapabilities',
            'UseDevelopmentAPNS',
        ]

        profile_hash_map = self._build_profile_hash_map()

        try:
            with open(file_path, 'r') as f:
                for line in f:
                    entry = json.loads(line)

                    data = {'source': entity_type}
                    for field in mdm_fields:
                        if field in entry:
                            data[field] = entry[field]

                    # Look up the profile stub SHA-256 hash
                    managing_id = entry.get('ManagingProfileIdentifier')
                    if managing_id and managing_id in profile_hash_map:
                        data['ProfileStubHash'] = profile_hash_map[managing_id]

                    mdm_entry = Event(
                        datetime=datetime.fromisoformat(entry.get('LastPollingAttempt')),
                        message=f"MDM Profile: {managing_id} with access rights {entry.get('AccessRights')}",
                        timestamp_desc='Last Polling Attempt',
                        module=self.module_name,
                        data=data
                    )

                    yield mdm_entry.to_dict()

        except FileNotFoundError as e:
            logger.warning(f'{entity_type} not found for {self.case_id}. {e}')
        except Exception as e:
            logger.exception(f'ERROR while extracting {entity_type} file. {e}')

    def __extract_plist_profile_events(self) -> Generator[dict, None, None]:
        """
        Extracts profile install/remove events from MCProfileEvents.plist.

        This file records a timeline of configuration profile operations (install, remove)
        along with the process that performed the action. Each profile event is yielded
        as a separate Event with a proper timestamp.

        :yield: A dictionary containing profile event details.
        """
        entity_type: str = 'logs_MCState_Shared_MCProfileEvents.plist.json'
        file_path: str = f'{self.parser.output_folder}/{entity_type}'

        profile_hash_map = self._build_profile_hash_map()

        try:
            with open(file_path, 'r') as f:
                data = json.loads(f.read())

            profile_events = data.get('ProfileEvents', [])
            for event_dict in profile_events:
                for profile_identifier, event_info in event_dict.items():
                    try:
                        timestamp = datetime.fromisoformat(event_info.get('Timestamp'))
                    except (ValueError, TypeError):
                        logger.warning(f'Invalid timestamp for profile event {profile_identifier}')
                        continue

                    operation = event_info.get('Operation', 'unknown')
                    process = event_info.get('Process', 'unknown')

                    event_data = {
                        'source': entity_type,
                        'ProfileIdentifier': profile_identifier,
                        'Operation': operation,
                        'Process': process,
                    }

                    # Look up the profile stub SHA-256 hash (try composite key first, then identifier only)
                    if profile_identifier in profile_hash_map:
                        event_data['ProfileStubHash'] = profile_hash_map[profile_identifier]
                    else:
                        # Try matching on just the PayloadIdentifier (strip the UUID suffix)
                        base_id = profile_identifier.rsplit('-', 5)[0] if '-' in profile_identifier else profile_identifier
                        if base_id in profile_hash_map:
                            event_data['ProfileStubHash'] = profile_hash_map[base_id]

                    profile_event = Event(
                        datetime=timestamp,
                        message=f"Profile {operation}: {profile_identifier} by {process}",
                        timestamp_desc=f'Profile {operation}',
                        module=self.module_name,
                        data=event_data
                    )

                    yield profile_event.to_dict()

        except FileNotFoundError as e:
            logger.warning(f'{entity_type} not found for {self.case_id}. {e}')
        except Exception as e:
            logger.exception(f'ERROR while extracting {entity_type} file. {e}')
