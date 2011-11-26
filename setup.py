#!/usr/bin/env python

# ...

from distutils.core import setup
from web import __version__

setup(name='Marmir',
      version=__version__,
      description='Marmir: makes spreadsheets easy',
      author='Brian Ray',
      author_email='brianhray@gmail.com',
      maintainer='Brian Ray',
      maintainer_email='brianhray@gmail.com',
      url='https://github.com/brianray/mm',
      packages=['mm', ],
      long_description="Python power spreadsheets on steroids",
#      license="Brian Ray", TBD
      platforms=["any"],
     )

