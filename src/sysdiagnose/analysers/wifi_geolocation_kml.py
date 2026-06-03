#! /usr/bin/env python3
"""
For Python3
Author: Aaron Kaplan <aaron@lo-res.org>
"""

import xml.etree.ElementTree as ET

from sysdiagnose.parsers.wifi_known_networks import WifiKnownNetworksParser
from sysdiagnose.utils.base import BaseAnalyserInterface, SysdiagnoseConfig


class WifiGeolocationKmlAnalyser(BaseAnalyserInterface):
    description = "Generate KML file for wifi geolocations"
    format = "kml"

    def __init__(self, config: SysdiagnoseConfig, case_id: str) -> None:
        super().__init__(__file__, config, case_id)

    def execute(self) -> str:
        json_data = WifiKnownNetworksParser(self.config, self.case_id).get_result()
        return WifiGeolocationKmlAnalyser.generate_kml_from_known_networks_json(json_data)

    # LATER merge this and wifi_geolocation.py to share as much common code as possible
    @staticmethod
    def generate_kml_from_known_networks_json(json_data: dict) -> str:
        """Generates KML XML string from known networks JSON data."""
        kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
        document = ET.SubElement(kml, "Document")

        # Add tour elements
        tour = ET.SubElement(document, "gx:Tour")
        ET.SubElement(tour, "name").text = "WiFi Tour"
        playlist = ET.SubElement(tour, "gx:Playlist")

        for network_name, network_data in json_data.items():
            ssid = network_data.get("SSID", network_name)
            timestamp_str = network_data.get("AddedAt", "")
            if not timestamp_str:
                timestamp_str = network_data.get("JoinedByUserAt", "")
            if not timestamp_str:
                timestamp_str = network_data.get("UpdatedAt", "")
            add_reason = network_data.get("AddReason", "")

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

                placemark = ET.SubElement(document, "Placemark")
                ET.SubElement(placemark, "name").text = ssid
                point = ET.SubElement(placemark, "Point")
                ET.SubElement(point, "coordinates").text = f"{lon},{lat},0"

                et_description = ET.SubElement(placemark, "description")
                et_description.text = description

                # Add to tour playlist  # TODO ideally the tour should be generated in the same order as the timestamps
                flyto = ET.SubElement(playlist, "gx:FlyTo")
                ET.SubElement(flyto, "gx:duration").text = "5.0"
                ET.SubElement(flyto, "gx:flyToMode").text = "smooth"
                camera = ET.SubElement(flyto, "Camera")
                ET.SubElement(camera, "longitude").text = str(lon)
                ET.SubElement(camera, "latitude").text = str(lat)
                ET.SubElement(camera, "altitude").text = "500"
                ET.SubElement(camera, "heading").text = "0"
                ET.SubElement(camera, "tilt").text = "45"
                ET.SubElement(camera, "roll").text = "0"

        # Use us-ascii encoding with xml_declaration to preserve compatibility with KML consumers.
        # This escapes non-ASCII characters as XML character references (e.g. &#233;),
        # matching the original behaviour of ET.ElementTree.write() and avoiding potential
        # ingestion issues with strict/older XML parsers that expect ASCII-safe content.
        return ET.tostring(kml, encoding="us-ascii", xml_declaration=True).decode("us-ascii")
