#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os, re
from setuptools import setup, find_packages

name = 'nipyper'
version = re.compile(r'VERSION\s*=\s*\((.*?)\)')

def get_package_version():
    "returns package version without importing it"
    base = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(base, name + "/__init__.py")) as initf:
        for line in initf:
            m = version.match(line.strip())
            if not m:
                continue
            return ".".join(m.groups()[0].split(", "))

classes = """
    Development Status :: 2 - Pre-Alpha
    Intended Audience :: Developers
    License :: OSI Approved :: MIT License
    Topic :: System :: Distributed Computing
    Framework :: Flask
    Operating System :: OS Independent
"""

## Potential additional classifiers, to be tested ##
    # Programming Language :: Python
    # Programming Language :: Python :: 2
    # Programming Language :: Python :: 2.6
    # Programming Language :: Python :: 2.7
    # Programming Language :: Python :: 3
    # Programming Language :: Python :: 3.3
    # Programming Language :: Python :: 3.4
    # Programming Language :: Python :: Implementation :: CPython
    # Programming Language :: Python :: Implementation :: PyPy

classifiers = [s.strip() for s in classes.split('\n') if s]

def main():
    setup(
        name = name,
        version = get_package_version(),
        author = 'Jyotishka Biswas',
        author_email = 'jyotishka.biswas@gmail.com',
        url = 'https://github.com/jyotishkabiswas/nipyper',
        description = 'A Flask server for creating, executing, and monitoring Nipype workflows.',
        license = 'MIT',
        test_suite = 'tests',
        packages = find_packages(exclude=['tests', 'tests.*']),
        classifiers = classifiers,
        entry_points = {
            'console_scripts': [
                'nipyper = nipyper.__main__:main'
            ]
        }
    )

if __name__ == '__main__':
    main()