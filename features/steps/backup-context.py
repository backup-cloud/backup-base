from backup_context import BackupContext
import random
import string
import os
import boto3
import sys


def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


def set_string_par(ssm, path: str, value: str) -> None:
    ssm_paramdef = dict(Name=path, Value=value, Type="String", Overwrite=True)
    eprint("putting: " + value + "into ssm param: " + path)
    ssm.put_parameter(**ssm_paramdef)


def ensure_s3_paths_in_ssm(s3_bucket: str, s3_path: str, ssm_path=None) -> None:
    ssm = boto3.client("ssm")
    set_string_par(ssm, ssm_path + "/s3_bucket", s3_bucket)
    set_string_par(ssm, ssm_path + "/s3_path", s3_path)


def ensure_encrypt_keys_in_s3() -> None:
    pass


@given(u"that I have a backup context configured")
def step_impl(context) -> None:
    context.random_test_prefix = "".join(
        [random.choice(string.ascii_letters + string.digits) for n in range(10)]
    )
    bname = context.s3_test_bucket = os.environ["S3_TEST_BUCKET"]
    s3path = context.s3_test_path = context.random_test_prefix
    context.s3_backup_target = context.s3_test_path + "/backup"
    context.ssm_path = "/testing/backup_context/" + context.random_test_prefix

    ensure_s3_paths_in_ssm(bname, s3path, ssm_path=context.ssm_path)
    ensure_encrypt_keys_in_s3()

    bc = BackupContext(ssm_path=context.ssm_path)
    context.backup_context = bc


@when(u"I request an encryption shell script")
def step_impl(context) -> None:
    context.shell_env = context.backup_context.make_shell()


@then(u"the script should encrypt my data")
def step_impl(context) -> None:
    raise NotImplementedError(u"STEP: Then the script should encrypt my data")
