# -*- coding: utf-8 -*-
import logging
import argparse
from ezcheck import download_ffl_db, parse_row
import os
logger = logging.getLogger('ezcheck')
logger.setLevel(logging.DEBUG)  # Collect all log levels
logger.addHandler(logging.NullHandler())  # Set the default logger to be a nullhandler


def download_ffl_database():
    """Download FFL List from ATF.gov"""
    parser = argparse.ArgumentParser()
    parser.add_argument("ffl", help="FFL number")
    parser.add_argument("filename", help="filename to download file to")
    args = parser.parse_args()
    print("Downloading FFL")
    file_obj = download_ffl_db(args.ffl, args.filename)
    print("Downloaded FFL Database to: %s" % file_obj.name)


def validate_data():
    """Parse a downloaded file from atf.gov"""
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="filename to parse/validate")
    args = parser.parse_args()
    if not os.path.isfile(args.filename):
        print("File doesn't exist: %s" % args.filename)
    print("Opening %s" % args.filename)
    unparsed_rows = [x for x in open(args.filename, 'r').readlines() if x and x != '\n']
    parsed_rows = []
    failed_rows = []
    exception_rows = []
    for i in unparsed_rows:
        try:
            if parse_row(i):
                parsed_rows.append(i)
            else:
                failed_rows.append(repr(i))
        except Exception as e:
            exception_rows.append((i, e))
    print("Successfully parsed %s of %s rows [Failures: %s, Exceptions: %s]" % (
        len(parsed_rows),
        len(unparsed_rows),
        len(failed_rows),
        len(exception_rows),
    ))
    if failed_rows:
        print("--- Rows failing parser:")
        print("\n".join(failed_rows))
    if exception_rows:
        print("--- Rows throwing python exceptions:")
        print("\n".join([x for x, y in exception_rows]))
        for row, exception in exception_rows:
            print("Row: {}\n--- Exception ---\n{}").format(row, exception)


if __name__ == '__main__':
    download_ffl_database()
