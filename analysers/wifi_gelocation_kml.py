#! /usr/bin/env python3

# For Python3
# Author: Aaron Kaplan <aaron@lo-res.org>

import sys
import json
# import dateutil.parser
from optparse import OptionParser

import xml.etree.ElementTree as ET


sys.path.append('..')   # noqa: E402
# from sysdiagnose import config        # noqa: E402


version_string = "sysdiagnose-wifi-geolocation-kml.py v2023-08-09 Version 0.2"

# ----- definition for analyse.py script -----#
# -----         DO NOT DELETE             ----#

analyser_description = "Generate KML file for wifi geolocations"
analyser_call = "generate_kml"
analyser_format = "json"


def generate_kml(jsonfile: str, outfile: str = "wifi-geolocations.kml"):
    """
    Modify the function to generate a KML file from Wi-Fi geolocation data and include a tour between the locations.
    Reads <jsonfile> as input and extracts all known Wi-Fi networks and their locations.
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
    json_data = json_entry

    # Create new KML root
    kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
    document = ET.SubElement(kml, 'Document')

    # Add tour elements
    tour = ET.SubElement(document, 'gx:Tour')
    ET.SubElement(tour, 'name').text = 'WiFi Tour'
    playlist = ET.SubElement(tour, 'gx:Playlist')

    for network_name, network_data in json_data.items():
        ssid = network_name
        lat = network_data.get('Latitude')
        lon = network_data.get('Longitude')

        if lat and lon:
            placemark = ET.SubElement(document, 'Placemark')
            ET.SubElement(placemark, 'name').text = ssid
            point = ET.SubElement(placemark, 'Point')
            ET.SubElement(point, 'coordinates').text = f"{lon},{lat},0"

            # Add to tour playlist
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
    tree.write(outfile)

    # Example usage:
    # generate_kml_with_tour('input_json_file.json', 'output_kml_file.kml')

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
                      help="KML file to save output")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(-1)

    if not options.inputfile and not options.outputfile:
        parser.error("Need to specify inputfile and outputfile")
    else:
        generate_kml(options.inputfile, outfile=options.outputfile)


# --------------------------------------------------------------------------- #

"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folks ;)
