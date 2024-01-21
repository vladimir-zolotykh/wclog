#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import os.path
import argparse
import xml.etree.ElementTree as ET


def convert_to_xml(input_file, output_file=None):
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + '.xml'
    with open(input_file, 'r') as file:
        lines = file.readlines()
    date = lines[0].strip()
    times = [line.strip() for line in lines[1:]]
    root = ET.Element("Root")
    date_element = ET.SubElement(root, "Date")
    date_element.text = date
    times_element = ET.SubElement(root, "Times")
    for time in times:
        time_element = ET.SubElement(times_element, "Time")
        time_element.text = time
    xml_tree = ET.ElementTree(root)
    with open(output_file, 'w') as xml_file:
        xml_tree.write(xml_file, encoding='unicode')


parser = argparse.ArgumentParser(description='Convert log text file to XML')
parser.add_argument('input_file')
parser.add_argument('--output-file')

if __name__ == '__main__':
    args = parser.parse_args()
    convert_to_xml(args.input_file, args.output_file)
