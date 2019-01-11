from backup_context import BackupContext
from unittest.mock import patch, ANY
from hamcrest import assert_that, equal_to
import random
import string
import os
import boto3
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def ensure_s3_paths_in_ssm(s3_path, ssm_path=None):
    ssm = boto3.client("ssm")
    s3_path_param = ssm_path + "/s3_base"
    ssm_paramdef = dict(
        Name=s3_path_param, Value=s3_path, Type="String", Overwrite=True
    )

    eprint("putting: " + s3_path + "into ssm param: " + s3_path_param)
    ssm.put_parameter(**ssm_paramdef)


def ensure_encrypt_keys_in_s3():
    pass


@given(u"that I have a backup context configured")
def step_impl(context):
    context.random_test_prefix = "".join(
        [random.choice(string.ascii_letters + string.digits) for n in range(10)]
    )
    context.s3_test_base = (
        os.environ["S3_TEST_BUCKET"] + "/" + context.random_test_prefix
    )
    context.s3_backup_target = context.s3_test_base + "/backup"
    context.ssm_path = "/testing/backup_context/" + context.random_test_prefix

    ensure_s3_paths_in_ssm(context.s3_test_base, ssm_path=context.ssm_path)
    ensure_encrypt_keys_in_s3()

    bc = BackupContext(ssm_path=context.ssm_path)
    context.bc = bc


@when(u"I request an encryption shell script")
def step_impl(context):
    context.shell_env = context.bc.make_shell()


@when(u"I run that script on a file")
def step_impl(context):
    context.bc.run_shell()


@then(u"environment variables and a script should be set up")
def step_impl(context):
    verify_script = """\
#!/bin/sh
if [ ! '$sys_backup_ssm_path' = '{}' ]
then
   echo wrong SSM path $ssm_path
fi\
"""
    context.bc.run_shell(verify_script)


@then(u"the script should encrypt my data")
def step_impl(context):
    raise NotImplementedError(u"STEP: Then the script should encrypt my data")


@when(u"I run a backup script from that context")
def step_impl(context):
    with patch("subprocess.run") as mockrun:
        context.result = context.bc.run("fakeprog")
        mockrun.assert_called_once_with(["fakeprog"], env=ANY)
        context.script_env = mockrun.call_args[1]["env"]


@then(u"my S3 URL should be configured")
def step_impl(context):
    assert_that(
        context.script_env["BACKUP_CONTEXT_S3_TARGET"],
        equal_to(context.s3_backup_target),
    )


@then(u"my encryption command should be configured")
def step_impl(context):
    assert_that(
        context.script_env["BACKUP_CONTEXT_ENCRYPT_COMMAND"], equal_to("backup_encrypt")
    )
