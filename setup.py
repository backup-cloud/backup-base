#!/usr/bin/env python

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="backup_cloud",
    version="0.1",
    author="Michael De La Rue",
    author_email="michael-paddle@fake.github.com",
    description="Backup your entire (AWS) cloud - base part",
    long_description=long_description,
    url="https://github.com/michael-paddle/backup-base",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
    ],
)
