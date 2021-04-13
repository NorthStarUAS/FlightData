#!/usr/bin/python3

from setuptools import setup, find_packages

setup(name='rcUAS_flightdata',
      version='1.3',
      description='Flight data management module',
      author='Curtis L. Olson',
      author_email='curtolson@flightgear.org',
      url='https://github.com/RiceCreekUAS',
      #package_dir = {'': 'aurauas'},
      #packages = ['aurauas_flightdata']
      packages = find_packages()
     )
