import gpg
import random
import string
import boto3
import os
import sys
from backup_cloud.base import BackupContext


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def setup_test_backup_context(ssm_path, s3_path, s3_test_bucket=None, recipients=None):
    """utility function to easily set up a context for testing

    sets up a context, given a pre-existing S3 bucket, and ensures
    that SSM is populated in order to be able to use the same backup
    location

    The bucket name can be specified with the s3_test_bucket parameter
    but will default to reading the S3_TEST_BUCKET environment
    variable if not set.

    """
    if s3_test_bucket is None:
        bname = s3_test_bucket = os.environ["S3_TEST_BUCKET"]
    else:
        bname = s3_test_bucket
    s3path = s3_path

    ensure_s3_paths_in_ssm(ssm_path, bname, s3path)

    return BackupContext(ssm_path=ssm_path, recipients=recipients)


def make_new_keypair(gpg_context: gpg.Context, userid: str = None):
    """create a new gpg keypair returning userid, public and private key

    utility function to create a new keypair.  In the case no userid
    is provided we will create a (partly) random one.
    """
    if not userid:
        userid = "backup-" + "".join(
            [random.choice(string.ascii_letters + string.digits) for n in range(10)]
        )

    # ubuntu bionic doesn't ahve key_export_minimial() so we fallback
    # in real life we can assume that the users would export using
    # some graphical tool.

    gpg_context.create_key(
        userid, algorithm="rsa3072", expires_in=31536000, encrypt=True
    )
    try:
        public_key = gpg_context.key_export_minimal(pattern=userid)
    except AttributeError:
        public_key = gpg_context.key_export(pattern=userid)

    private_key = gpg_context.key_export_secret(pattern=userid)

    return userid, public_key, private_key


def set_string_par(ssm, path: str, value: str) -> None:
    ssm_paramdef = dict(Name=path, Value=value, Type="String", Overwrite=True)
    eprint("putting: " + value + "into ssm param: " + path)
    ssm.put_parameter(**ssm_paramdef)


def ensure_s3_paths_in_ssm(ssm_path: str, s3_bucket: str, s3_path: str) -> None:
    """utility function used to configure ssm parameters for test runs

    s3_bucket: the bucket used for backup
    s3_path: base path under which backup folders will be
    """
    ssm = boto3.client("ssm")
    set_string_par(ssm, ssm_path + "/s3_bucket", s3_bucket)
    set_string_par(ssm, ssm_path + "/s3_path", s3_path)
