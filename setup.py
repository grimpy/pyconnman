#!/usr/bin/env python

from distutils.core import setup
import glob, os

setup(name='pyconnman',
      version='0.1',
      description='Python Connman Client',
      author='Jo De Boeck',
      author_email='deboeck.jo@gmail.com',
      url='http://github.com/grimpy/pyconnman',
      packages=['connman', 'connman/ui'] ,
      scripts=['connman-gtk'],
      data_files=[('share/pixmaps/connman', glob.glob('icons/*.png')),
                  ('share/connman/ui/', glob.glob('connman/ui/*.xml'))]
     )
