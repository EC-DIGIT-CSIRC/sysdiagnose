#! /usr/bin/env python3
"""
For Python3
Author: Aaron Kaplan <aaron@lo-res.org>
"""

import dateutil.parser
import gpxpy
import gpxpy.gpx

from sysdiagnose.parsers.wifi_known_networks import WifiKnownNetworksParser
from sysdiagnose.utils.base import BaseAnalyserInterface, SysdiagnoseConfig, logger


class WifiGeolocationAnalyser(BaseAnalyserInterface):
    description = "Generate GPS Exchange (GPX) of wifi geolocations"
    format = "gpx"

    def __init__(self, config: SysdiagnoseConfig, case_id: str) -> None:
        super().__init__(__file__, config, case_id)

    def execute(self) -> str:
        json_data = WifiKnownNetworksParser(self.config, self.case_id).get_result()
        return WifiGeolocationAnalyser.generate_gpx_from_known_networks_json(json_data)

    @staticmethod
    def generate_gpx_from_known_networks_json(json_data: dict) -> str:
        """Generates GPX XML string from known networks JSON data."""
        gpx = gpxpy.gpx.GPX()

        for network_name, network_data in json_data.items():
            ssid = network_data.get("SSID", network_name)
            timestamp_str = network_data.get("AddedAt", "")
            if not timestamp_str:
                timestamp_str = network_data.get("JoinedByUserAt", "")
            if not timestamp_str:
                timestamp_str = network_data.get("UpdatedAt", "")
            add_reason = network_data.get("AddReason", "")

            try:
                timestamp = dateutil.parser.parse(timestamp_str)
            except Exception:
                logger.exception(
                    f"Error converting timestamp. Timestamp was: {timestamp_str!s}. Assuming Jan 1st 1970."
                )
                timestamp = dateutil.parser.parse("1970-01-01")

            bssid = network_data.get("__OSSpecific__", {}).get("BSSID", "")
            channel = network_data.get("__OSSpecific__", {}).get("CHANNEL", "")
            for bss in network_data.get("BSSList", []):
                lat = bss.get("LocationLatitude", "")
                lon = bss.get("LocationLongitude", "")
                location_accuracy = bss.get("LocationAccuracy", "")

                description = f"""BSSID: {bssid}
    Channel: {channel}
    Timestamp: {timestamp_str}
    LocationAccuracy: {location_accuracy}
    Latitude: {lat}
    Longitude: {lon}
    Reason for Adding: {add_reason}"""

                waypoint = gpxpy.gpx.GPXWaypoint(latitude=lat, longitude=lon, time=timestamp)
                waypoint.name = ssid
                waypoint.description = description
                gpx.waypoints.append(waypoint)

        return gpx.to_xml()
