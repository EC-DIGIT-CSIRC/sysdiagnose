#! /usr/bin/env python3

# For Python3
# Author: Aaron Kaplan <aaron@lo-res.org>

import sys
import json
import dateutil.parser
from optparse import OptionParser
import os
import gpxpy
import gpxpy.gpx

sys.path.append('..')   # noqa: E402
import config        # noqa: E402


version_string = "sysdiagnose-demo-analyser.py v2023-04-28 Version 0.1"

# ----- definition for analyse.py script -----#
# -----         DO NOT DELETE             ----#

analyser_description = "Generate GPS Exchange (GPX) of wifi geolocations"
analyser_call = "analyse_path"
analyser_format = "gpx"


def analyse_path(case_folder: str, outfile: str = "wifi-geolocations.gpx") -> bool:
    potential_source_files = ['wifinetworks/WiFi_com.apple.wifi.known-networks.plist.json', 'plists/WiFi_com.apple.wifi.known-networks.plist.json', 'wifi_known_networks.json']
    input_file_path = None
    for fname in potential_source_files:
        input_file_path = os.path.join(case_folder, fname)
        if os.path.isfile(input_file_path):
            break
    if not input_file_path:
        # TODO we could call the parser and generate the file for us...and then parse it...
        raise FileNotFoundError(f"Could not find any of the potential source files: {potential_source_files}.")

    # we have a valid file_path and can generate the gpx file
    with open(input_file_path, 'r') as f:
        json_data = json.load(f)
    return generate_gpx_from_known_networks_json(json_data=json_data, outfile=outfile)


def generate_gpx(jsonfile: str, outfile: str = "wifi-geolocations.gpx"):
    """
    Generate the GPX file in <filename>. Reads <jsonfile> as input and extracts all known-wifi-networks and their locations.

    Sample input JSON snippet:
    ```json
    """
    try:
        with open(jsonfile, 'r') as fp:
            json_data = json.load(fp)
    except Exception as e:
        print(f"Error while parsing inputfile JSON. Reason: {str(e)}")
        sys.exit(-1)

    json_entry = json_data.get('com.apple.wifi.known-networks.plist')
    if not json_entry:
        print("Could not find the 'com.apple.wifi.known-networks.plist' section. Bailing out.", file=sys.stderr)
        sys.exit(-2)
    json_data = json_entry      # start here


def generate_gpx_from_known_networks_json(json_data: str, outfile: str):

    # Create new GPX object
    gpx = gpxpy.gpx.GPX()

    for network_name, network_data in json_data.items():
        ssid = network_data.get('SSID', network_name)
        # timestamps are always tricky
        timestamp_str = network_data.get('AddedAt', '')
        if config.debug:
            print(f"AddedAt: {timestamp_str}")
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

            # Create new waypoint
            waypoint = gpxpy.gpx.GPXWaypoint(latitude=lat, longitude=lon, time=timestamp)
            waypoint.name = ssid
            waypoint.description = f'''BSSID: {bssid}
                Channel: {channel}
                Timestamp: {timestamp_str}
                LocationAccuracy: {location_accuracy}
                Latitude: {lat}
                Longitude: {lon}
                Reason for Adding: {add_reason}'''

            # Add waypoint to gpx file
            gpx.waypoints.append(waypoint)

        # Save gpx file
        with open(outfile, 'w') as f:
            f.write(gpx.to_xml())
    return


# --------------------------------------------------------------------------- #
"""
    Main function
"""


def main():

    print(f"Running {version_string}\n")

    usage = "\n%prog -d JSON directory\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile",
                      action="store", type="string",
                      help="JSON file from parsers")
    parser.add_option("-o", dest="outputfile",
                      action="store", type="string",
                      help="GPX file to save output")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)

    if not options.inputfile and not options.outputfile:
        parser.error("Need to specify inputfile and outputfile")
    else:
        generate_gpx(options.inputfile, outfile=options.outputfile)


# --------------------------------------------------------------------------- #

"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folks ;)
