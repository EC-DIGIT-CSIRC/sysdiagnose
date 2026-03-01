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

        except FileNotFoundError:
            logger.debug(f'{entity_type} not found for {self.case_id} (device not MDM-enrolled)')
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

        except FileNotFoundError:
            logger.debug(f'{entity_type} not found for {self.case_id}')
        except Exception as e:
            logger.exception(f'ERROR while extracting {entity_type} file. {e}')

    def __extract_plist_vpn_profiles(self) -> Generator[dict, None, None]:
        """
        Extracts VPN and network extension profile configurations from the
        NetworkExtension plist.

        Parses each NEConfiguration entry from com.apple.networkextension.plist,
        extracting VPN tunnel details such as provider bundle identifiers, server
        addresses, on-demand rules, and tunnel settings. Non-VPN network extension
        entries (content filters, DNS settings) are also captured.

        Uses the sysdiagnose creation timestamp since VPN configs are a point-in-time
        snapshot with no individual timestamps.

        :yield: A dictionary containing VPN profile details.
        """
        entity_type: str = 'logs_Networking_com.apple.networkextension.plist.json'
        file_path: str = f'{self.parser.output_folder}/{entity_type}'

        # Map numeric tunnel types to human-readable names
        tunnel_type_map = {
            1: 'PacketTunnel',
            2: 'AppProxy',
            3: 'IPSec',
            4: 'IKEv2',
        }

        # Map numeric on-demand action values to names
        on_demand_action_map = {
            1: 'Connect',
            2: 'Disconnect',
            3: 'EvaluateConnection',
            4: 'Ignore',
        }

        # Map numeric interface type match values
        interface_type_map = {
            0: 'Any',
            1: 'Ethernet',
            2: 'WiFi',
            3: 'Cellular',
        }

        snapshot_time = self.sysdiagnose_creation_datetime

        try:
            with open(file_path, 'r') as f:
                data = json.loads(f.read())

            for config_uuid, config_entry in data.items():
                if not isinstance(config_entry, dict):
                    continue

                # Skip metadata keys (Version, Generation, Index, etc.)
                if 'VPN' not in config_entry and 'ContentFilter' not in config_entry and 'DNSSettings' not in config_entry:
                    continue

                name = config_entry.get('Name', '')
                application = config_entry.get('Application', '')
                application_name = config_entry.get('ApplicationName', '')

                vpn_config = config_entry.get('VPN')
                content_filter = config_entry.get('ContentFilter')
                dns_settings = config_entry.get('DNSSettings')

                # Determine the extension type
                if isinstance(vpn_config, dict) and vpn_config:
                    extension_type = 'VPN'
                elif isinstance(content_filter, dict) and content_filter:
                    extension_type = 'ContentFilter'
                elif isinstance(dns_settings, dict) and dns_settings:
                    extension_type = 'DNSSettings'
                else:
                    extension_type = 'Other'

                event_data = {
                    'source': entity_type,
                    'ConfigUUID': config_uuid,
                    'Name': name,
                    'Application': application,
                    'ApplicationName': application_name,
                    'ExtensionType': extension_type,
                    'Grade': config_entry.get('Grade'),
                    'AlwaysOnVPN': config_entry.get('AlwaysOnVPN'),
                }

                # Extract VPN-specific fields
                if extension_type == 'VPN' and isinstance(vpn_config, dict):
                    raw_tunnel_type = vpn_config.get('TunnelType')
                    event_data['TunnelType'] = tunnel_type_map.get(raw_tunnel_type, raw_tunnel_type)
                    event_data['Enabled'] = vpn_config.get('Enabled', False)
                    event_data['OnDemandEnabled'] = vpn_config.get('OnDemandEnabled', False)
                    event_data['DisconnectOnDemandEnabled'] = vpn_config.get('DisconnectOnDemandEnabled', False)

                    # Resolve on-demand rules with human-readable values
                    raw_rules = vpn_config.get('OnDemandRules', [])
                    if isinstance(raw_rules, list) and raw_rules:
                        resolved_rules = []
                        for rule in raw_rules:
                            if isinstance(rule, dict):
                                resolved_rule = {}
                                raw_action = rule.get('Action')
                                resolved_rule['Action'] = on_demand_action_map.get(raw_action, raw_action)
                                raw_iface = rule.get('InterfaceTypeMatch')
                                resolved_rule['InterfaceTypeMatch'] = interface_type_map.get(raw_iface, raw_iface)
                                # Include non-empty match criteria
                                for match_key in ('SSIDMatch', 'DNSSearchDomainMatch', 'DNSServerAddressMatch', 'ProbeURL'):
                                    val = rule.get(match_key)
                                    if val:
                                        resolved_rule[match_key] = val
                                resolved_rules.append(resolved_rule)
                        event_data['OnDemandRules'] = resolved_rules

                    # Extract protocol details
                    protocol = vpn_config.get('Protocol')
                    if isinstance(protocol, dict):
                        event_data['ServerAddress'] = protocol.get('ServerAddress', '')
                        event_data['NEProviderBundleIdentifier'] = protocol.get('NEProviderBundleIdentifier', '')
                        event_data['IncludeAllNetworks'] = protocol.get('IncludeAllNetworks', False)
                        event_data['ExcludeLocalNetworks'] = protocol.get('ExcludeLocalNetworks', False)
                        event_data['EnforceRoutes'] = protocol.get('EnforceRoutes', False)
                        event_data['DisconnectOnSleep'] = protocol.get('DisconnectOnSleep', False)

                        vendor_config = protocol.get('VendorConfiguration')
                        if isinstance(vendor_config, dict) and vendor_config:
                            event_data['VendorConfiguration'] = vendor_config

                # Build message
                status_parts = []
                if event_data.get('Enabled'):
                    status_parts.append('enabled')
                if event_data.get('OnDemandEnabled'):
                    status_parts.append('on-demand')
                status_str = f" ({', '.join(status_parts)})" if status_parts else ''

                display_name = application_name or name or application or config_uuid
                message = f"NetworkExtension {extension_type}: {display_name}{status_str}"

                vpn_event = Event(
                    datetime=snapshot_time,
                    message=message,
                    timestamp_desc='Sysdiagnose Creation',
                    module=self.module_name,
                    data=event_data
                )

                yield vpn_event.to_dict()

        except FileNotFoundError:
            logger.debug(f'{entity_type} not found for {self.case_id}')
        except Exception as e:
            logger.exception(f'ERROR while extracting {entity_type} file. {e}')
