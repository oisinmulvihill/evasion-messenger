"""
Project's setuptool configuration.

This should eggify and in theory upload to pypi without problems.

Oisin Mulvihill
2008-12-23

"""
import os
from setuptools import setup, find_packages

Name='evasion-messenger'
ProjectUrl="" #http://github.com/oisinmulvihill/evasion-messenger/tarball/master#egg=evasion_messenger"
Version='1.2.0'
Author='Oisin Mulvihill'
AuthorEmail='oisinmulvihill at gmail dot com'
Maintainer=' Oisin Mulvihill'
Summary='A Python ZeroMQ Pub/Sub Implementation and Messaging library.'
License='Evasion Project CDDL License'
ShortDescription=Summary

# Add the README text if the file is present (not in egg).
detailed = Summary
if os.path.isfile("README.rst"):
    with file("README.rst", "r") as fd:
        detailed = fd.read()

Description = detailed


needed = [
    'pyzmq',
    'evasion-common==1.0.2',
]

# needed for < python 2.6
#    'simplejson',


EagerResources = [
    'evasion',
]

ProjectScripts = [
]

PackageData = {
    '': ['*.*'],
}

EntryPoints = """
    [console_scripts]
    messagehub = evasion.messenger.hub:main
"""

setup(
    url=ProjectUrl,
    name=Name,
    zip_safe=False,
    version=Version,
    author=Author,
    author_email=AuthorEmail,
    description=ShortDescription,
    long_description=Description,
    license=License,
    scripts=ProjectScripts,
    install_requires=needed,
    setup_requires=[
      'nose>=1.0.0',
    ],
    test_suite="nose.collector",
    entry_points=EntryPoints,
    packages=find_packages('lib'),
    package_data=PackageData,
    package_dir = {'': 'lib'},
    eager_resources = EagerResources,
    namespace_packages = ['evasion'],
)
