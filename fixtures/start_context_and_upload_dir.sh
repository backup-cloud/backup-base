#!/bin/sh

# this script shows the use of backup_cloud file encryption to encrypt a
# directory and put it.   This 

set -evx

# # if you are starting on a fresh machine you might run something like the following:

# python3 -m venv backup_cloud_venv
# source  backup_cloud_venv/bin/activate
# # hardwired since right now there's no way to link to "latest stable" 
# pip install https://github.com/backup-cloud/backup-base/archive/20190603113026-fcb88b0.tar.gz

SSM_PATH=$1
DIRECTORY=$2
S3_PATH=$3

if [ "$3" = "" ]
then
    cat <<EOF >&2
start_context_and_upload_dir: missing argument

 usage: start_context_and_upload_dir ssm_path directory s3_path

     ssm_path - path in ssm where configuration will be found
     directory - directory containing files to backup
     s3_path - *relative* path in S3 to upload files

EOF
    exit 5
fi

STARTUP="$(start-backup-context "$SSM_PATH")"
echo "startup output: $STARTUP"
eval "$STARTUP"
if [ "$BACKUP_CONTEXT_UPLOAD_COMMAND" = "" ]
then
    echo BACKUP_CONTEXT_UPLOAD_COMMAND variable is not defined aborting >&2
    exit 5
fi
if [ "$BACKUP_CONTEXT_UPLOAD_COMMAND" = "" ]
then
    echo BACKUP_CONTEXT_UPLOAD_COMMAND variable is not defined aborting >&2
    exit 5
fi
"$BACKUP_CONTEXT_UPLOAD_COMMAND" "$DIRECTORY" "$S3_PATH"
