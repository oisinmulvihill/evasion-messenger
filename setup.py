"""
Project's setuptool configuration.

This should eggify and in theory upload to pypi without problems.

Oisin Mulvihill
2008-12-23

"""
from setuptools import setup, find_packages

Name='evasion-messenger'
ProjectUrl="" #http://github.com/oisinmulvihill/evasion-messenger/tarball/master#egg=evasion_messenger"
Version='1.2.dev1'
Author='Oisin Mulvihill'
AuthorEmail='oisinmulvihill at gmail dot com'
Maintainer=' Oisin Mulvihill'
Summary='Messaging library used to package and delivery events'
License='Evasion Project CDDL License'
ShortDescription=Summary
Description=Summary

TestSuite = 'evasion.messenger.tests'

needed = [
    'pydispatcher',
    'pyzmq',
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
    test_suite=TestSuite,
    scripts=ProjectScripts,
    install_requires=needed,
    packages=find_packages('lib'),
    package_data=PackageData,
    package_dir = {'': 'lib'},
    eager_resources = EagerResources,
    namespace_packages = ['evasion'],
)
