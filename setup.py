#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'requests>=2.13.0',
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='ezcheck',
    version='0.5.0',
    description="Library for downloading, validating federal firearms licensees using the ATF eZCheck application.",
    long_description=readme + '\n\n' + history,
    author="James Pleger",
    author_email='jpleger@gmail.com',
    url='https://github.com/jpleger/ezcheck',
    packages=[
        'ezcheck',
    ],
    py_modules=['ezcheck.cli', 'ezcheck.core'],
    entry_points={
        'console_scripts': [
            'ezcheck-download=ezcheck.cli:download_ffl_database',
            'ezcheck-validate=ezcheck.cli:validate_data',
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords='ezcheck',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
