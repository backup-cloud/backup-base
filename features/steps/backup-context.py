from backup_context import BackupContext
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


@given(u"that I have a backup context configured")
def step_impl(context) -> None:
    bname = context.s3_test_bucket = os.environ["S3_TEST_BUCKET"]
    s3path = context.s3_test_path
    context.s3_backup_target = context.s3_test_path + "/backup"
    context.ssm_path = "/testing/backup_context/" + context.random_test_prefix

    ensure_s3_paths_in_ssm(bname, s3path, ssm_path=context.ssm_path)

    bc = BackupContext(ssm_path=context.ssm_path, recipients=context.gpg_userlist)
    context.backup_context = bc


@when(u"I request an encryption shell script")
def step_impl(context) -> None:
    context.shell_env = context.backup_context.make_shell()


@then(u"the script should encrypt my data")
def step_impl(context) -> None:
    raise NotImplementedError(u"STEP: Then the script should encrypt my data")
