# -*- coding: utf-8 -*-
import requests
import time
import logging
import os
import tempfile
import struct
from datetime import datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  # Ran into issues with the certificate
logger = logging.getLogger('ezcheck')
logger.setLevel(logging.DEBUG)  # Collect all log levels
logger.addHandler(logging.NullHandler())  # Set the default logger to be a nullhandler
CONSOLE_LOG_FORMATTER = logging.Formatter('%(asctime)s: %(message)s')
DEBUG_LOG_FORMATTER = logging.Formatter('[%(funcName)s-%(levelname)s] %(asctime)s: %(message)s')
FFL_DOWNLOAD_URL = 'https://fflezcheck.atf.gov/fflezcheck/fflDownload.do'
FFL_DOWNLOAD_OPTION_MAPPING = {
    'licRegn': 'FFLRegion',
    'licDist': 'FFLDistrict',
    'licCnty': 'FFLCounty',
    'licType': 'FFLType',
    'licXprdte': 'FFLExpiration',
    'licSeqn': 'FFLSequence',
}

DEFAULT_FILENAME = '/tmp/ffldb-%s' % time.strftime('%Y-%m-%d')



#
# We take the slices and offsets that are provided by the ATF to create a usable db
OFFSET_STRUCT = '15s50s50s50s30s2s9s50s30s2s9s10s8s8s'
FFL_STRUCT = '1s2s3s2s2s5s'
FIELD_NAMES = ['FFLNumber', 'LicenseName', 'BusinessName', 'BusinessStreet', 'BusinessCity', 'BusinessState',
               'BusinessZipCode', 'MailingStreet', 'MailingCity', 'MailingState', 'MailingZipCode', 'Telephone',
               'LOAIssueDate', 'LOAExpirationDate']


def parse_ffl_number(ffl_number, parse_values=True):
    """
    This take an FFL number a dictionary representation of the appropriate fields
    :param ffl_number: String with the FFL number, this can be in the format of X-XX-XXX-XX-XX-XXXXX or just the string
    :param parse_values: Parse the values as an int or string, int is useful for working in databases
    :return: dict of parsed FFL number
    """
    ffl_number = ffl_number.replace('-', '')
    if len(ffl_number) != 15:
        raise ValueError('Invalid ffl Length: %s for %s' % (len(ffl_number), ffl_number))
    if parse_values:
        render = int
    else:
        render = str
    return {
        'FFLRegion': render(ffl_number[0]),
        'FFLDistrict': render(ffl_number[1:3]),
        'FFLCounty': render(ffl_number[3:6]),
        'FFLType': render(ffl_number[6:8]),
        'FFLExpiration': ffl_number[8:10],
        'FFLSequence': render(ffl_number[10:]),
        'FFLNumber': ffl_number,
    }


def parse_zipcode(zipcode):
    """
    This function takes a zipcode and returns a split out zipcode and the +4 for the post office.

    :param zipcode: Zipcode
    :return: zipcode, zipcodeplus
    """
    # We like to work with the zipcode as a string, since we can slice part of the number.
    zipcode = str(zipcode)
    plus = None
    # Check to see if this is a 9 digit zipcode.. if so, pull the appropriate slice.
    if len(str(zipcode)) == 9:
        # Zipcode can be valid and not include the +4
        try:
            plus = int(zipcode[5:])
        except ValueError:
            plus = 0
        # Slice the zipcode
        zipcode = zipcode[:5]
    # This can't fail, if it does... entire number is bad!
    try:
        zipcode = int(zipcode)
    except ValueError:
        return None, None
    return zipcode, plus


def parse_row(row):
    """
    This function takes an individual row and parses it

    :param row: row to process (from ATF ffl download)
    :return: parsed dict of row
    """
    # If this isn't a valid entry, just return silently
    if len(row) != 324:
        return False
    # TODO: Do something if this shit fails
    structured_data = struct.unpack(OFFSET_STRUCT, row.strip('\n'))
    parsed_entry = dict(zip(FIELD_NAMES, [x.strip().upper() for x in structured_data]))

    # Format/parse the zipcode and clean it up
    for zipcode in ['BusinessZipCode', 'MailingZipCode']:
        # Replace any dashes that are in the zipcode...
        parsed_entry[zipcode].replace('-', '')
        # Parse the zipcode, converting to int and put in the PlusFour entry
        parsed_entry[zipcode], parsed_entry['%sPlusFour' % zipcode] = parse_zipcode(parsed_entry.get(zipcode))

    # Convert loa to datetime object
    for loa_date in ['LOAExpirationDate', 'LOAIssueDate']:
        # This is an uncommon field, which is the Letter of Authorization, which allows an FFL to do business while
        # their license has expired. Only 20-30% of the total FFLs will have these entries.
        if parsed_entry[loa_date]:
            parsed_entry[loa_date] = datetime.strptime(parsed_entry.get(loa_date), '%m%d%Y')
        else:
            parsed_entry[loa_date] = None
    # Extract all the stuff from the FFL
    parsed_entry.update(parse_ffl_number(parsed_entry.get('FFLNumber')))

    # Cleanup the telephone as a int
    # Who knew telephones were optional... :)
    try:
        parsed_entry['Telephone'] = int(parsed_entry.get('Telephone'))
    except ValueError:
        parsed_entry['Telephone'] = 0
    return parsed_entry


def download_ffl_db(ffl_number, filename=None, file_object=None):
    """
    Uses requests to download a copy of the current FFL licensees

    :param ffl_number: What the FFL number to download the file is
    :param filename: which file it should be output to
    :param file_object: A file like object passed to the function will override any filenames that are set
    :return: filename that was written to
    """
    # If no filename is specified and no file object specified, create a temp file for the download filename
    if not filename and not file_object:
        filename = tempfile.mkstemp(prefix='ffl-')[1]

    # If no file_object is passed, create a new file like object
    if not file_object:
        file_object = open(filename, 'wb')

    params = {'Search': 'Download'}
    # Parse and properly map the FFL number to the correct fields so we can download the file.

    logger.info('Starting download from ATF site using %s' % file_object)
    ffl = parse_ffl_number(ffl_number, parse_values=False)
    for field, value in FFL_DOWNLOAD_OPTION_MAPPING.items():
        params[field] = ffl[value]
    # Post to the ATF url to start the download
    request = requests.post(FFL_DOWNLOAD_URL, data=params, verify=False)
    # Validate that the file has started to download
    if 'content-disposition' not in request.headers or 'attachment' not in request.headers['content-disposition']:
        file_object.write(request.content)
        logger.fatal('We received an invalid response from the ATF... Aborting')
        raise ValueError("Invalid Response from ATF")
    file_object.write(request.content)
    logger.debug('Wrote %s bytes' % len(request.content))
    return file_object
