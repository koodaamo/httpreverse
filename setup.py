#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ["pyaml", "jinja2", "xmltodict"]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='httpreverse',
    version='0.4.0',
    description="Reverse-engineer legacy HTTP APIs",
    long_description=readme + '\n\n' + history,
    author="Petri Savolainen",
    author_email='petri@koodaamo.fi',
    url='https://github.com/koodaamo/httpreverse',
    packages=[
        'httpreverse',
    ],
    package_dir={'httpreverse':
                 'httpreverse'},
    include_package_data=True,
    install_requires=requirements,
    license="GNU General Public License v3",
    zip_safe=False,
    keywords='httpreverse',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
