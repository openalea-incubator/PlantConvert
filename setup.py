# -*- coding: utf-8 -*-

from __future__ import absolute_import
import sys
import os

from setuptools import setup, find_packages

name = 'OpenAlea.PlantConvert'

description = "OpenAlea.PlantConvert is an OpenAlea package to convert a plant to / from a `mtg`format to a wide range of other formats"
readme = open('README.md').read()
history = open('HISTORY.rst').read()

# find version number in src/plantconvert/version.py
version = {}
with open("src/plantconvert/version.py") as fp:
    exec(fp.read(), version)

authors="Shenyuan Ma, Christophe Pradal, Thomas Arsouze, Rémi Vézy"
authors_email="mashenyuancn@gmail.com, @pradal, @thomasarsouze, @VEZY"

license = 'cecill-c'
# dependencies to other eggs
install_requires= ["openalea.mtg", "openalea.plantgl", "vtk", "pygltflib", "numpy"],

# find packages
packages = find_packages('src')
package_dir={'': 'src'}

setup(
    name=name,
    version=version["__version__"],
    description=description,
    long_description=description,
    author=authors,
    author_email=authors_email,
    license=license,
    keywords='MTG, openalea, .opf, format, plantconvert',

    # package installation
    packages=packages,
    package_dir=package_dir,

    # Namespace packages creation by deploy
    #namespace_packages=['openalea'],
    zip_safe=False,

    # Dependencies
    install_requires=install_requires,

    #include_package_data=True,

    # (you can provide an exclusion dictionary named exclude_package_data to remove parasites).
    # alternatively to global inclusion, list the file to include
    #package_data={'': ['*.csv', '*.mtg', '*.R*', '*.ipynb']},

    # Declare scripts and wralea as entry_points (extensions) of your package
    #entry_points={'wralea': ['strawberry = openalea.strawberry_wralea']},
    )