#!/bin/sh

# this script shows the use of backup_cloud file encryption to encrypt a
# file locally.  It is designed to be run from python code.

set -evx

if [ -z "$BACKUP_CONTEXT_ENCRYPT_COMMAND" ]
then
    echo "no backup command variable set" >&2
    exit 5
fi
$BACKUP_CONTEXT_ENCRYPT_COMMAND testdata.dat testdata.dat.gpg
