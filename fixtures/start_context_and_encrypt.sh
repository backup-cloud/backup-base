#!/bin/sh

# this script shows the use of backup_cloud file encryption to encrypt a
# file locally.   This 

set -evx

# # if you are starting on a fresh machine you might run something like the following:

# python3 -m venv backup_cloud_venv
# source  backup_cloud_venv/bin/activate
# # hardwired since right now there's no way to link to "latest stable" 
# pip install https://github.com/backup-cloud/backup-base/archive/20190603113026-fcb88b0.tar.gz
SSM_PATH=$1

STARTUP="$(start_backup_context "$SSM_PATH")"
echo "startup output: $STARTUP"
eval "$STARTUP"
$BACKUP_CONTEXT_ENCRYPT_COMMAND testdata.dat testdata.dat.gpg
