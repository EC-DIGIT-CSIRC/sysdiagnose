#! /usr/bin/env python3

# For Python3
# Analyse the results produced by parsers
import sys


version_string = "analyse.py v2023-04-27 Version 1.0"

# --------------------------------------------------------------------------- #
"""
    Main function
"""
def main():

    if sys.version_info[0] < 3:
        print("Must be using Python 3! Exiting ...")
        exit(-1)

    print("Running " + version_string + "\n")
    return

"""
   Call main function
"""
if __name__ == "__main__":

    # Create an instance of the Analysis class (called "base") and run main
    main()

# That's all folks ;)