#! /usr/bin/env python3

# For Python3
# Script to parse ./logs/olddsc files
# Author: david@autopsit.org
#
#
import os
import sys
import json
from optparse import OptionParser
import xml.etree.ElementTree as ElementTree

version_string = "sysdiagnose-olddsc.py v2020-02-26 Version 1.0"

# ----- definition for parsing.py script -----#
# -----         DO NET DELETE             ----#

parser_description = "Parsing olddsc files"
parser_input = "olddsc"
parser_call = "get_olddsc"

# --------------------------------------------#


def parse_olddsc_file(file, output):
    """
        Parse OLDDSC file

        File level metadata:
        --------------------
        <key>Architecture</key>
        <string>arm64</string>
        <key>Binaries</key>
        <key>Cache_UUID_String</key>
        <string>98C199D7-FF2A-3B05-8D17-247ECD74F732</string>
        <key>Unslid_Base_Address</key>
        <integer>6442450944</integer>

    Each entry look like:
        ---------------------
        <dict>
            <key>Load_Address</key>
            <integer>6442696704</integer>
            <key>Path</key>
            <string>/usr/lib/system/libsystem_trace.dylib</string>
            <key>Text_Segment_Size</key>
            <integer>94208</integer>
            <key>UUID_String</key>
            <string>4EB9C273-180A-3301-AA68-262A68EB0028</string>
        </dict>
    """
    tree = ElementTree.parse(file)
    root = tree.getroot()

    # Parse header
    olddsc = {}
    header = root.find('dict')
    txts = header.findall("string")
    ints = header.findall("integer")
    olddsc["Architecture"] = txts[0].text
    olddsc["Cache_UUID_String"] = txts[1].text
    olddsc["Unslid_Base_Address"] = int(ints[0].text)

    # Parse entries
    entries = []
    for array in root.findall('dict/array'):
        for entry in array.findall('dict'):
            ints = entry.findall("integer")
            txts = entry.findall("string")
            load_address = int(ints[0].text)
            path = txts[0].text
            text_segment_size = int(ints[1].text)
            uuid = txts[1].text
            jentry = {
                "Load_Address": load_address,
                "Path": path,
                "Text_Segment_Size": text_segment_size,
                "UUID_String": uuid
            }
            entries.append(jentry)
    olddsc["Binaries"] = entries
    saveJson(entries, output)
    return True


def saveJson(text, output):
    jsontext = json.dumps(text, indent=4)
    try:
        # open file descriptor
        fd = sys.stdout
        if (output is not sys.stdout):
            fd = open(output, "w")

        # dump JSON
        fd.write(jsontext)

        # close file descriptor
        if (fd is not sys.stdout):
            fd.close()
    except Exception as e:
        print(f"Impossible to save to JSON to {output}. Reason: {str(e)}\n")
    return


def get_olddsc(folder, ios_version=13, output=sys.stdout):
    # check if folder exists and is really a folder
    if (not (os.path.exists(folder) and os.path.isdir(folder))):
        print("%s is not a valid folder!" % folder)
        return False
    # list all files in the folder and parse files
    # r=root, d=directories, f = files
    for r, d, f in os.walk(folder):
        for file in f:
            parse_olddsc_file("%s/%s" % (folder, file), output)
    return True

# --------------------------------------------------------------------------- #


"""
    Main function
"""


def main():

    if sys.version_info[0] < 3:
        print("Must be using Python 3! Exiting ...")
        exit(-1)

    print("Running " + version_string + "\n")

    usage = "\n%prog -i inputfile\n"

    parser = OptionParser(usage=usage)
    parser.add_option("-i", dest="inputfile",
                      action="store", type="string",
                      help="Provide path to ./logs/olddsc directory")
    (options, args) = parser.parse_args()

    # no arguments given by user, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        exit(-1)

    # parse PS file :)
    if options.inputfile:
        get_olddsc(options.inputfile)
    else:
        print("WARNING -i option is mandatory!")

# --------------------------------------------------------------------------- #


"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()


# That's all folk ;)
