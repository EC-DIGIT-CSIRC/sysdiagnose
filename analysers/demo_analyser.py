#! /usr/bin/env python3

# For Python3
# DEMO - Skeleton

import json


analyser_description = "Do something useful (DEMO)"
analyser_format = "json"


def analyse_path(case_folder: str, output_file: str = "demo-analyser.json") -> bool:
    """
    Generate the timeline and save it to filename
    """
    print("DO SOMETHING HERE")
    with open(output_file, 'w') as f:
        json.dump({"Hello": "World"}, f, indent=4)
    return
