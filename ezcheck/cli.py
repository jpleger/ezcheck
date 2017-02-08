# -*- coding: utf-8 -*-
import logging
import click
from ezcheck import download_ffl_db
logger = logging.getLogger('ezcheck')
logger.setLevel(logging.DEBUG)  # Collect all log levels
logger.addHandler(logging.NullHandler())  # Set the default logger to be a nullhandler


@click.command()
@click.option('--ffl', envvar='FFL_NUMBER', prompt=True)
@click.option('--filename')
def download_ffl_database(ffl, filename=None):
    """Download FFL List from ATF.gov"""
    click.echo("Starting Download using eZCheck")
    file_path = download_ffl_db(ffl, filename)
    click.echo("Downloaded FFL Database to: %s" % file_path)

if __name__ == '__main__':
    download_ffl_database()