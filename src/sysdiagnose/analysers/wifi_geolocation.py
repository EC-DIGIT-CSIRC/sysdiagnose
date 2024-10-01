#! /usr/bin/env python3

# For Python3
# Author: Aaron Kaplan <aaron@lo-res.org>

import dateutil.parser
import gpxpy
import gpxpy.gpx
from sysdiagnose.utils.base import BaseAnalyserInterface
from sysdiagnose.parsers.wifi_known_networks import WifiKnownNetworksParser


class WifiGeolocationAnalyser(BaseAnalyserInterface):
    description = "Generate GPS Exchange (GPX) of wifi geolocations"
    format = "gpx"

    def __init__(self, config: dict, case_id: str):
        super().__init__(__file__, config, case_id)

    def get_result(self, force: bool = False):
        raise NotImplementedError("This function is not compatible with this module.")

    def save_result(self, force: bool = False, indent=None):
        self.execute()

    def execute(self):
        json_data = WifiKnownNetworksParser(self.config, self.case_id).get_result()
        return WifiGeolocationAnalyser.generate_gpx_from_known_networks_json(json_data=json_data, output_file=self.output_file)

    def generate_gpx_from_known_networks_json(json_data: str, output_file: str):
        # Create new GPX object
        gpx = gpxpy.gpx.GPX()

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

            try:
                timestamp = dateutil.parser.parse(timestamp_str)
            except Exception as e:
                print(f"Error converting timestamp. Reason: {str(e)}. Timestamp was: {str(timestamp_str)}. Assuming Jan 1st 1970.")
                timestamp = dateutil.parser.parse('1970-01-01')     # begin of epoch

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
                waypoint = gpxpy.gpx.GPXWaypoint(latitude=lat, longitude=lon, time=timestamp)
                waypoint.name = ssid
                waypoint.description = description

                # Add waypoint to gpx file
                gpx.waypoints.append(waypoint)

            # Save gpx file
            with open(output_file, 'w') as f:
                f.write(gpx.to_xml())
        return
