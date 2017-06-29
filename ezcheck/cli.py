# -*- coding: utf-8 -*-
import logging
import argparse
from ezcheck import download_ffl_db
logger = logging.getLogger('ezcheck')
logger.setLevel(logging.DEBUG)  # Collect all log levels
logger.addHandler(logging.NullHandler())  # Set the default logger to be a nullhandler


def download_ffl_database():
    """Download FFL List from ATF.gov"""
    parser = argparse.ArgumentParser()
    parser.add_argument("ffl", help="FFL number")
    parser.add_argument("filename", help="filename to download file to")
    args = parser.parse_args()
    print "Downloading FFL"
    ffl = str(args.ffl).replace('-','')
    file_path = download_ffl_db(ffl, args.filename)
    print "Downloaded FFL Database to: %s" % file_path

if __name__ == '__main__':
    download_ffl_database()