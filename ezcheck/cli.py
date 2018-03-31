# -*- coding: utf-8 -*-
import logging
import argparse
import os
import sys
import json
from ezcheck.core import download_ffl_db, parse_file, parse_ffl_number
from ezcheck.core import logger, CONSOLE_LOG_FORMATTER, DEBUG_LOG_FORMATTER


parent_parser = argparse.ArgumentParser(add_help=False)
parent_parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                           help='verbose mode (loglevel: debug)')
parent_parser.add_argument('-s', '--silent', action='store_true', dest='silent',
                           help='disable console output')
parent_parser.add_argument('-l', '--log', default=None, dest='logfile', help='logfile to write to')


def setup_logging(args):
    if not args.silent:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(CONSOLE_LOG_FORMATTER)
        logger.addHandler(stream_handler)
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    if args.logfile:
        file_handler = logging.FileHandler(args.logfile)
        file_handler.setFormatter(DEBUG_LOG_FORMATTER)
        logger.addHandler(file_handler)


def download_ffl_database():
    """Download FFL List from ATF.gov"""
    parser = argparse.ArgumentParser(parents=[parent_parser, ])
    parser.add_argument('-t', '--testing', action='store_true', dest='testing')
    parser.add_argument('ffl', help='FFL Number')
    parser.add_argument('filename', help='filename to write download')
    args = parser.parse_args()
    setup_logging(args)
    logger.debug('FFL: %s' % args.ffl)
    try:
        parse_ffl_number(args.ffl)
    except ValueError:
        logger.critical('Invalid FFL')
        sys.exit(-1)
    logger.info("Downloading FFL")
    file_object = open(args.filename, 'wb+')
    download_ffl_db(args.ffl, file_object)
    logger.info("Downloaded FFL Database to: %s" % file_object.name)


def dump_json():
    parser = argparse.ArgumentParser(parents=[parent_parser, ])
    args = parser.parse_args()
    setup_logging(args)


def validate_data():
    """Parse a downloaded file from atf.gov"""
    parser = argparse.ArgumentParser(parents=[parent_parser, ])
    parser.add_argument("filename", help="filename to parse/validate")
    args = parser.parse_args()
    setup_logging(args)
    if not os.path.isfile(args.filename):
        logger.critical("File doesn't exist: %s" % args.filename)
    logger.info("Opening %s" % args.filename)
    parsed_data = parse_file(open(args.filename, 'r'))
    logger.info('Finished Load')
    logger.info(json.dumps(parsed_data[0], sort_keys=True, indent=4, separators=(',', ': ')))
    logger.info(json.dumps(parsed_data[-1], sort_keys=True, indent=4, separators=(',', ': ')))


if __name__ == '__main__':
    sys.exit(-1)
