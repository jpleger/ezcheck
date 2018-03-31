#!/usr/bin/env python
"""
EZCheck Core
"""
import requests
import logging
import os
from datetime import datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  # Ran into issues with the certificate
logger = logging.getLogger('ezcheck')
logger.setLevel(logging.INFO)  # Collect all log levels
CONSOLE_LOG_FORMATTER = logging.Formatter('%(asctime)s: %(message)s')
DEBUG_LOG_FORMATTER = logging.Formatter('[%(funcName)s-%(levelname)s] %(asctime)s: %(message)s')


FFL_DOWNLOAD_URL = 'https://fflezcheck.atf.gov/fflezcheck/fflDownload.do'
FFL_DOWNLOAD_LABELS = (
    'licRegn',
    'licDist',
    'licCnty',
    'licType',
    'licXprdte',
    'licSeqn',
)
FFL_LABELS = (
    'FFLRegion',
    'FFLDistrict',
    'FFLCounty',
    'FFLType',
    'FFLExpiration',
    'FFLSequence',
    'LicenseName',
    'BusinessName',
    # 'BusinessStreet',
    # 'BusinessCity',
    # 'BusinessState',
    # 'BusinessZipCode',
    # 'MailingStreet',
    # 'MailingCity',
    # 'MailingState',
    # 'MailingZipCode',
    'Telephone',
    'LOAIssueDate',
    'LOAExpirationDate',
)
ADDRESS_LABELS = (
    'Street',
    'City',
    'State',
    'ZipCode',
    'ZipCodePlus',
)
BYTE_OFFSETS = (1, 2, 3, 2, 2, 5, 50, 50, 50, 30, 2, 9, 50, 30, 2, 9, 10, 8, 8, 1)
# ffl Number (License Number)	1-15
# License Name	16-65
# Business Name	66-115
# Business Street	116-165
# Business City	166-195
# Business State	196-197
# Business Zip Code	198-206
# Mailing Street	207-256
# Mailing City	257-286
# Mailing State	287-288
# Mailing Zip Code	289-297
# Voice Telephone	298-307
# LOA Issue Date	308-315(MMDDYYYY)
# LOA Expiration Date	316-323(MMDDYYYY)


def parse_ffl_number(ffl_number, labels=FFL_LABELS[:6]):
    """
    Take an FFL and parse it into a dictionary with the appropriate labels.

    :param ffl_number: String with the FFL number, this can be in the format of X-XX-XXX-XX-XX-XXXXX or just the string
    :param labels: a list of labels (6 total) for the dictionary returned from the function
    :return: a parsed ffl number
    """
    if len(labels) != 6:
        logger.debug(repr(labels))
        raise TypeError('Invalid list of labels or data passed to parser')
    ffl_number = str(ffl_number).replace('-', '')
    if len(ffl_number) != 15:
        logger.debug(ffl_number)
        raise ValueError('Invalid length of FFL ID')

    # Go through the offsets and create a parsed FFL number
    parsed_ffl_number = []
    offset = 0
    for byte_offset in BYTE_OFFSETS[:6]:
        parsed_ffl_number.append(ffl_number[offset:offset+byte_offset])
        offset += byte_offset

    # Create a new dictionary and return.
    parsed_ffl_number = dict(zip(labels, parsed_ffl_number))
    return parsed_ffl_number


def parse_zipcode(zipcode):
    """
    Take a zipcode and returns a split out zipcode and the +4 for the post office.

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


def download_ffl_db(ffl_number, file_object):
    """
    Uses requests to download a copy of the current FFL licensees

    :param ffl_number: What the FFL number to download the file is
    :param filename: which file it should be output to
    :param file_object: A file like object passed to the function will override any filenames that are set
    :return: filename that was written to
    """
    # Check the file object and validate that it is writable:
    if not hasattr(file_object, 'writable') or not file_object.writable():
        raise ValueError('Invalid file_object passed to download_ffl_db')
    logger.info('Starting download from ATF site using %s' % file_object)

    # Setup the post data for download
    params = {'Search': 'Download'}

    # Parse and properly map the FFL number to the correct fields for post so we can download the file.
    ffl_params = parse_ffl_number(ffl_number, FFL_DOWNLOAD_LABELS)
    params.update(ffl_params)

    # Post to the ATF url and params to start the download
    response = requests.post(FFL_DOWNLOAD_URL, data=params, verify=False, stream=True)

    # Validate that the file has started to download
    if 'content-disposition' not in response.headers or 'attachment' not in response.headers['content-disposition']:
        # close the request and write the content
        if response.content and response.headers:
            file_object.write('response headers:\n')
            file_object.write(repr(response.headers))
            file_object.write('\nparams:')
            file_object.write(repr(params))
            file_object.write('\n')
            file_object.write('request response:\n')
            file_object.write(response.content)
            file_object.write('\n')
        logger.fatal('We received an invalid response from the ATF... Aborting download')
        file_object.flush()
        raise ValueError("Invalid Response from ATF")
    else:
        # Read chunks from the request streaming:
        chunks = 0
        for chunk in response.iter_content(chunk_size=1024):
            chunks += 1
            if not chunks % 1000:
                logger.debug('%iMB Downloaded' % (chunks/1000))
            file_object.write(chunk)
        file_object.flush()
    return file_object, response


def parse_file(file_object):
    """
    Parse a FFL dump file, given a file descriptor.

    :param file_object: File descriptor
    :return:
    """
    if not hasattr(file_object, 'seekable') or not file_object.seekable():
        raise IOError('fd provided is not seekable')
    if not hasattr(file_object, 'readable') or not file_object.readable():
        raise IOError('fd provided is not readable')

    # Determine the file size
    file_size = file_object.seek(0, 2)

    # Determine if we need to decode the file as bytes
    decode_bytes = False
    if type(file_object.read(1)) is bytes:
        decode_bytes = True

    # Move pointer to first position in file to skip newline
    file_object.seek(1, 0)
    results = []

    # Loop through each line, using the BYTE_OFFSETS to read each row, discard the newline
    while True:
        # Performance testing to figure out the best way to parse/load the data and normalize.
        # Disk read operation: ~1.5 seconds/run
        r = list(map(file_object.read, BYTE_OFFSETS))[:19]

        # If the file is being read as bytes instead of a string, we need to decode before using str
        if decode_bytes:
            r = list(map(bytes.decode, r))

        # Strip spaces: ~.5 seconds/run
        r = list(map(str.strip, r))

        # Forcing Upppercase: ~1 second/run
        r = list(map(str.upper, r))

        # Zipcode Normalization: ~.5 seconds/run
        business_address = r[8:12]
        del(r[8:12])
        business_address.extend(parse_zipcode(business_address.pop()))
        mailing_address = r[8:12]
        del(r[8:12])
        mailing_address.extend(parse_zipcode(mailing_address.pop()))

        # Format to dictionary: ~1 second/run
        ffl_id = r[:6]
        r = dict(zip(FFL_LABELS, r))
        r.update({'BusinessAddress': dict(zip(ADDRESS_LABELS, business_address))})
        r.update({'MailingAddress': dict(zip(ADDRESS_LABELS, mailing_address))})
        r.update({'FFLNumber': '-'.join(ffl_id)})
        results.append(r)
        if file_object.tell() >= file_size:
            break
    return results
