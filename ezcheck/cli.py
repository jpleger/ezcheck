# -*- coding: utf-8 -*-
import logging
import click
logger = logging.getLogger('ezcheck')
logger.setLevel(logging.DEBUG)  # Collect all log levels
logger.addHandler(logging.NullHandler())  # Set the default logger to be a nullhandler


@click.command()
@click.option('--ffl', envvar='FFL_NUMBER', prompt=True)
@click.option('--filename')
def download_ffl_list(ffl, filename=None):
    """Download FFL List from ATF.gov"""
    click.echo("Starting Download using eZCheck")
    click.echo(ffl)
    click.echo(filename)

if __name__ == '__main__':
    download_ffl_list()