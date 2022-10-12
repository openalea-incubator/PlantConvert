# -*- coding: utf-8 -*-

from __future__ import absolute_import
import sys
import os

from setuptools import setup, find_packages

name = 'OpenAlea.PlantConvert'
version = '0.0.1'

description = "plantconvert is a package for converting mtg into different file formats"
long_description = open('readme.md').read()

authors="Shenyuan Ma"
authors_email="mashenyuancn@gmail.com"

license = 'cecill-c'
# dependencies to other eggs
setup_requires = ['openalea.mtg',
"openalea.plantgl",
"vtk",
"pygltflib",
"numpy"
]

# find packages
packages = find_packages('src')
package_dir={'': 'src'}

setup(
    name=name,
    version=version,

    description=description,
    long_description=long_description,
    author=authors,
    author_email=authors_email,
    license=license,
    keywords='MTG, openalea',

    # package installation
    packages=packages,
    package_dir=package_dir,

    # Namespace packages creation by deploy
    #namespace_packages=['openalea'],
    zip_safe=False,

    # Dependencies
    setup_requires=setup_requires,

    #include_package_data=True,

    # (you can provide an exclusion dictionary named exclude_package_data to remove parasites).
    # alternatively to global inclusion, list the file to include
    #package_data={'': ['*.csv', '*.mtg', '*.R*', '*.ipynb']},

    # Declare scripts and wralea as entry_points (extensions) of your package
    #entry_points={'wralea': ['strawberry = openalea.strawberry_wralea']},
    )