from backup_cloud.test_support import setup_test_backup_context
import sys
from typing import Any

given: Any
when: Any
then: Any


def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


@given(u"that I have prepared my account with definitions for backups")
@given(u"that I have a backup context configured with matching users")
def step_impl_0(context) -> None:
    context.ssm_path = "/testing/backup_context/" + context.random_test_prefix

    bc = context.backup_context = setup_test_backup_context(
        ssm_path=context.ssm_path,
        s3_path=context.s3_test_path,
        recipients=context.gpg_userlist,
    )
    context.s3_backup_target = bc.s3_path() + "/backup"


@given(
    u"that I have a backup context configured with matching users with incorrect s3_path"
)
def step_impl_1(context) -> None:
    context.ssm_path = "/testing/backup_context/" + context.random_test_prefix

    bc = context.backup_context = setup_test_backup_context(
        ssm_path=context.ssm_path,
        s3_path="/" + context.s3_test_path,
        recipients=context.gpg_userlist,
    )
    context.s3_backup_target = bc.s3_path() + "/backup"


@when(u"I configure a backup context")
def step_impl_2(context) -> None:
    context.ssm_path = "/testing/backup_context/" + context.random_test_prefix

    bc = context.backup_context = setup_test_backup_context(
        ssm_path=context.ssm_path, s3_path=context.s3_test_path
    )
    context.s3_backup_target = bc.s3_path() + "/backup"


@when(u"I request an encryption shell script")
def step_impl_3(context) -> None:
    context.shell_env = context.backup_context.make_shell()
