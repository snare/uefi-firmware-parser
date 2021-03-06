#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os

from uefi_firmware.uefi import *
from uefi_firmware.generator import uefi as uefi_generator
from uefi_firmware import AutoParser

def _process_show_extract(parsed_object):
    parsed_object.process()
    if not args.quiet:
        parsed_object.showinfo('')

    if args.extract:
        print "Dumping..."
        parsed_object.dump(args.output)


def brute_search_volumes(data):
    volumes = search_firmware_volumes(data)
    for index in volumes:
        parse_firmware_volume(data[index - 40:], name=index - 40)
    pass


def parse_firmware_volume(data, name=0):
    firmware_volume = FirmwareVolume(data, name)
    if not firmware_volume.valid_header:
        return
    _process_show_extract(firmware_volume)

    if args.generate is not None:
        print "Generating FDF..."
        firmware_volume.dump(args.generate)
        generator = uefi_generator.FirmwareVolumeGenerator(firmware_volume)
        path = os.path.join(args.generate, "%s-%s.fdf" % (args.generate, name))
        dump_data(path, generator.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse, and optionally output, details and data on UEFI-related firmware.")
    parser.add_argument(
        '-b', "--brute", action="store_true",
        help='The input is a blob and may contain FV headers.')

    parser.add_argument('-q', "--quiet",
                        default=False, action="store_true", help="Do not show info.")
    parser.add_argument('-o', "--output",
                        default=".", help="Dump EFI Files to this folder.")
    parser.add_argument('-e', "--extract",
                        action="store_true", help="Extract all files/sections/volumes.")
    parser.add_argument('-g', "--generate",
                        default=None, help="Generate a FDF, implies extraction (volumes only)")
    parser.add_argument("--test",
                        default=False, action='store_true', help="Test file parsing, output name/success.")
    parser.add_argument("file", nargs='+', help="The file(s) to work on")
    args = parser.parse_args()

    for file_name in args.file:
        try:
            with open(file_name, 'rb') as fh:
                input_data = fh.read()
        except Exception, e:
            print "Error: Cannot read file (%s) (%s)." % (file_name, str(e))
            continue

        if args.brute:
            brute_search_volumes(input_data)
            continue

        parser = AutoParser(input_data)
        if args.test:
            print "%s: %s" % (file_name, red(parser.type()))
            continue

        if parser.type() is 'unknown':
            print "Error: cannot parse %s, could not detect firmware type." % (file_name)
            continue

        firmware = parser.parse()
        _process_show_extract(firmware)
