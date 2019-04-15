from backup_cloud import BackupContext
from backup_cloud.base import ensure_s3_paths_in_ssm
import os
import sys
from typing import Any

given: Any
when: Any
then: Any


def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


@given(u"that I have a backup context configured with matching users")
def step_impl(context) -> None:
    bname = context.s3_test_bucket = os.environ["S3_TEST_BUCKET"]
    s3path = context.s3_test_path
    context.s3_backup_target = context.s3_test_path + "/backup"
    context.ssm_path = "/testing/backup_context/" + context.random_test_prefix

    ensure_s3_paths_in_ssm(context.ssm_path, bname, s3path)

    bc = BackupContext(ssm_path=context.ssm_path, recipients=context.gpg_userlist)
    context.backup_context = bc


@when(u"I configure a backup context")
def step_impl_0(context) -> None:
    bname = context.s3_test_bucket = os.environ["S3_TEST_BUCKET"]
    s3path = context.s3_test_path
    context.s3_backup_target = context.s3_test_path + "/backup"
    context.ssm_path = "/testing/backup_context/" + context.random_test_prefix

    ensure_s3_paths_in_ssm(context.ssm_path, bname, s3path)

    bc = BackupContext(ssm_path=context.ssm_path)
    context.backup_context = bc


@when(u"I request an encryption shell script")
def step_impl_1(context) -> None:
    context.shell_env = context.backup_context.make_shell()
