#! /usr/bin/env python3

# For Python3
# Analyse the results produced by parsers
import os
import sys
import glob
import tabulate
import importlib

version_string = "analyse.py v2023-04-27 Version 1.0"


def list_analysers(folder):
    """
        List available anlysers
    """
    os.chdir(folder)
    modules = glob.glob(os.path.join(os.path.dirname('.'), "*.py"))
    lines = []
    for analyser in modules:
        try:
            spec = importlib.util.spec_from_file_location(analyser[:-3], analyser)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            line = [analyser[:-3], module.analyser_description]
            lines.append(line)
        except:     # noqa: E722
            continue

    headers = ['Analyser Name', 'Parser Description']

    print(tabulate(lines, headers=headers))

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