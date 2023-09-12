#! /usr/bin/env python3

# For Python3
# Author: Aaron Kaplan <aaron@lo-res.org>

import os
import sys
import json
from datetime import datetime
import dateutil.parser
from optparse import OptionParser

from pykml.factory import KML_ElementMaker as KML
from pykml.factory import GX_ElementMaker as GX
from lxml import etree

sys.path.append('..')   # noqa: E402
from sysdiagnose import config        # noqa: E402


version_string = "wifiGeolocationKML.py v2023-08-12 Version 0.1"

# ----- definition for analyse.py script -----#
# -----         DO NET DELETE             ----#

analyser_description = "Generate GPS Exchange (GPX) of wifi geolocations"
analyser_call = "generate_gpx"
analyser_format = "json"


def generate_kml(jsonfile: str, outfile: str = "wifi-geolocations.gpx"):
    """
    Generate the KML file in <filename>. Reads <jsonfile> as input and extracts all known-wifi-networks and their locations.
    KML files include more information for generating a "tour" (fly-through)

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

    # start with a base KML tour and playlist
    tour_doc = KML.kml(
        KML.Document(
            GX.Tour(
                KML.name("com.apple.wifi.known-networks "),
                GX.Playlist(),
            )
        )
    )

    for network_name, network_data in json_data.items():
        ssid = network_name
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

            # fly to the point
            tour_doc.Document[gxns+"Tour"].Playlist.append(
                GX.FlyTo(
                    GX.duration(5),  # adjust as needed
                    GX.flyToMode("smooth"),
                    KML.LookAt(
                        KML.longitude(lon),
                        KML.latitude(lat),
                        KML.altitude(0),
                        KML.heading(0),
                        KML.tilt(0),
                        KML.range(10000000.0),  # adjust as needed
                        KML.altitudeMode("relativeToGround"),
                    )
                ),
            )

            waypoint.description = f'''BSSID: {bssid}
                Channel: {channel}
                Timestamp: {timestamp_str}
                LocationAccuracy: {location_accuracy}
                Latitude: {lat}
                Longitude: {lon}
                Reason for Adding: {add_reason}'''

            # add a placemark for the point
            tour_doc.Document.append(
                KML.Placemark(
                    KML.name(ESSID),
                    KML.description(waypoint.description),
                    KML.Point(
                        KML.extrude(1),
                        KML.altitudeMode("relativeToGround"),
                        KML.coordinates(f"{lon},{lat},10"),
                    )
                )
            )

        # write the KML document to a file
        with open('my_tour.kml', 'w') as outfile:
            outfile.write(etree.tostring(tour_doc, pretty_print=True).decode())
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
