#! /usr/bin/env python3

# For Python3
# Author: Aaron Kaplan <aaron@lo-res.org>

import xml.etree.ElementTree as ET
from sysdiagnose.utils.base import BaseAnalyserInterface
from sysdiagnose.parsers.wifi_known_networks import WifiKnownNetworksParser


class WifiGeolocationKmlAnalyser(BaseAnalyserInterface):
    description = "Generate KML file for wifi geolocations"
    format = "kml"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_result(self, force: bool = False):
        raise NotImplementedError("This function is not compatible with this module.")

    def save_result(self, force: bool = False, indent=None):
        self.execute()

    def execute(self):
        json_data = WifiKnownNetworksParser(self.config, self.case_id).get_result()
        # we have a valid file_path and can generate the gpx file
        return WifiGeolocationKmlAnalyser.generate_kml_from_known_networks_json(json_data=json_data, output_file=self.output_file)

    # LATER merge this and wifi_geolocation.py to share as much common code as possible
    def generate_kml_from_known_networks_json(json_data: str, output_file: str):
        # Create new KML root
        kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
        document = ET.SubElement(kml, 'Document')

        # Add tour elements
        tour = ET.SubElement(document, 'gx:Tour')
        ET.SubElement(tour, 'name').text = 'WiFi Tour'
        playlist = ET.SubElement(tour, 'gx:Playlist')

        for network_name, network_data in json_data.items():
            ssid = network_data.get('SSID', network_name)
            # timestamps are always tricky
            timestamp_str = network_data.get('AddedAt', '')
            if not timestamp_str:
                timestamp_str = network_data.get('JoinedByUserAt', '')      # second best attempt
            if not timestamp_str:
                timestamp_str = network_data.get('UpdatedAt', '')           # third best attempt
            # Convert ISO 8601 format to datetime
            add_reason = network_data.get("AddReason", '')

            # try:
            #     timestamp = dateutil.parser.parse(timestamp_str)
            # except Exception as e:
            #     print(f"Error converting timestamp. Reason: {str(e)}. Timestamp was: {str(timestamp_str)}. Assuming Jan 1st 1970.")
            #     timestamp = dateutil.parser.parse('1970-01-01')     # begin of epoch

            bssid = network_data.get('__OSSpecific__', {}).get('BSSID', '')
            channel = network_data.get('__OSSpecific__', {}).get('CHANNEL', '')
            for bss in network_data.get('BSSList', []):
                lat = bss.get('LocationLatitude', '')
                lon = bss.get('LocationLongitude', '')
                location_accuracy = bss.get('LocationAccuracy', '')

                description = f'''BSSID: {bssid}
    Channel: {channel}
    Timestamp: {timestamp_str}
    LocationAccuracy: {location_accuracy}
    Latitude: {lat}
    Longitude: {lon}
    Reason for Adding: {add_reason}'''

                # Create new waypoint
                placemark = ET.SubElement(document, 'Placemark')
                ET.SubElement(placemark, 'name').text = ssid
                point = ET.SubElement(placemark, 'Point')
                ET.SubElement(point, 'coordinates').text = f"{lon},{lat},0"

                et_description = ET.SubElement(placemark, 'description')
                et_description.text = description

                # Add to tour playlist  # TODO ideally the toor should be generated in the same order as the timestamps
                flyto = ET.SubElement(playlist, 'gx:FlyTo')
                ET.SubElement(flyto, 'gx:duration').text = '5.0'  # Duration of each flyto
                ET.SubElement(flyto, 'gx:flyToMode').text = 'smooth'
                camera = ET.SubElement(flyto, 'Camera')
                ET.SubElement(camera, 'longitude').text = str(lon)
                ET.SubElement(camera, 'latitude').text = str(lat)
                ET.SubElement(camera, 'altitude').text = '500'  # Camera altitude
                ET.SubElement(camera, 'heading').text = '0'
                ET.SubElement(camera, 'tilt').text = '45'
                ET.SubElement(camera, 'roll').text = '0'

        # Convert the ElementTree to a string and save it to a file
        tree = ET.ElementTree(kml)
        tree.write(output_file)

        return
