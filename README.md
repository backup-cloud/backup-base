This is a base layer for our automated backup which provides the
simple service of backing up from S3 locations into encrypted files in
other S3 locations.

backup_context.BackupContext
============================

The main class provided in this repo is a context class which reads
configuration from S3 and handles backup encryption for you.

    >>> from backup_cloud import BackupContext
    >>> rcp = ["test@example.com"] 
    >>> bc = BackupContext(ssm_path="/bc-demo", recipients=rcp)
    >>> cp = bc.run("myscript.sh")
    >>> print(cp.stdout.decode('UTF-8').strip())
    *********************
    backing up everything
    *********************

Makefile Goals
==============

prepare
-------

This will run ansible to set up your account.  See Ansible based
deployment below.  Obviously you need to have (a reasonably recent)
ansible installed first.

test and other subgoals
-----------------------

The various subgoals of test run all the tests.

all: (default)
--------------

This will run through the preparation and all the tests.

Ansible based deployment
========================

There are two ansible scripts included which prepare for testing.

- `prepare-account.yml` - this is for setting up accounts needed for
  other parts - it needs to be run with full AWS admin privilages to be
  able to set up the accounts used for testing.

- `prepare-test-enc-backup.yml` - this is required to setup the
  account where testing will happen.  This needs to be run from an
  account which is able to create S3 buckets.

Status and getting releases
===========================

Releases are currently created automatically in the case of succesfull
automated testing.  You can simply take the latest one from
[the Release page](https://github.com/michael-paddle/backup-base/releases).

Builds are run in travis:
[![Build Status](https://travis-ci.org/michael-paddle/backup-base.svg?branch=tested)](https://travis-ci.org/michael-paddle/backup-base)