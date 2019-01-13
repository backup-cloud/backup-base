from typeguard import typechecked  # type: ignore
from os import environ
from backup_context import ensure_s3_paths_in_ssm
import boto3
import random
import string
from subprocess import run
from behave_ansible import call_ansible_step
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


@typechecked(always=True)
@given(u"I have an S3 bucket for backup testing")
def step_impl(context) -> None:
    call_ansible_step(
        context.this_step.step_type + " " + context.this_step.name,
        playbook="test-enc-backup.yml",
    )


@typechecked(always=True)
@given(u"that I have configured my settings in SSM")
def step_impl(context) -> None:
    bname = context.s3_test_bucket = environ["S3_TEST_BUCKET"]
    s3path = context.s3_test_path
    context.s3_backup_target = context.s3_test_path + "/backup"
    context.ssm_path = "/testing/backup_context/" + context.random_test_prefix

    ensure_s3_paths_in_ssm(context.ssm_path, bname, s3path)


@typechecked(always=True)
@given(u"that I have an S3 backup bucket where I have write access")
def step_impl(context) -> None:
    # we are using the same bucket so this can be empty for now
    pass


@typechecked(always=True)
@given(u"that I have a file in S3 to backup")
def step_impl(context) -> None:
    context.test_data = "".join(
        [random.choice(string.ascii_letters + string.digits) for n in range(16)]
    ).encode("utf-8")
    context.store_bucket.put_object(
        Key="origin/" + context.test_key, Body=context.test_data
    )


@typechecked(always=True)
@when(u"I run my backup script giving it the base path in SSM")
def step_impl(context) -> None:
    run(
        args=[
            "./backup.py",
            "--ssm-base",
            "test/system-backup/backup-test-" + context.test_key,
        ]
    )


@typechecked(always=True)
@then(u"a backup should be created in the S3 destination bucket")
def step_impl(context) -> None:
    client = boto3.client("s3")
    o_name = "backup/s3/" + context.test_key
    obj = context.store_bucket.Object(o_name)
    try:
        res = obj.get()
    except client.exceptions.NoSuchKey as e:
        eprint("couldn't access missing object: " + o_name)
        raise (e)

    context.encrypted_file_contents = res["Body"].read()
