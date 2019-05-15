#!/usr/bin/env python

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="backup_cloud",
    version="0.2",
    author="Michael De La Rue",
    author_email="michael-paddle@fake.github.com",
    description="Backup your entire (AWS) cloud - base part",
    long_description=long_description,
    url="https://github.com/michael-paddle/backup-base",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
    ],
    # python gpgme (the official library distributed by the GPG team)
    # has to be installed by the operating system so we don't include
    # it here so that PIP does not attempt to install it!
    install_requires=["boto3"],
)
