from typeguard import typechecked  # type: ignore
from os import environ
from backup_cloud.base import ensure_s3_paths_in_ssm
from backup_cloud.s3 import backup_s3_to_s3
import boto3
import random
import string
from subprocess import run
from behave_ansible import call_ansible_step
from hamcrest import assert_that, greater_than
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
    context.s3_src_file_path = s3_src_file = "origin/" + context.testdir_random_id
    context.store_bucket.put_object(Key=s3_src_file, Body=context.test_data)


@typechecked(always=True)
@when(u"I request a backup of that file using the context")
def step_impl(context):
    backup_context = context.backup_context
    src_bucket = context.store_bucket.name
    src_path = context.s3_src_file_path
    dest_bucket = context.backup_bucket.name
    dest_path = context.s3_test_path + "/backup-test/individual-file-backup.gpg"
    backup_s3_to_s3(backup_context, src_bucket, src_path, dest_bucket, dest_path)
    context.s3_dest_path = dest_path


@typechecked(always=True)
@when(u"I run my backup script giving it the base path in SSM")
def step_impl(context) -> None:
    run(args=["./backup.py", "--ssm-base", context.ssm_path])


@typechecked(always=True)
@then(u"a backup object should be created in the S3 destination bucket")
def step_impl(context) -> None:
    client = boto3.client("s3")
    o_name = context.s3_dest_path
    obj = context.store_bucket.Object(o_name)
    try:
        res = obj.get()
    except client.exceptions.NoSuchKey as e:
        eprint("couldn't access missing object: " + o_name)
        raise (e)

    context.encrypted_file_contents = res["Body"].read()
    assert_that(
        len(context.encrypted_file_contents),
        greater_than(15),
        "backup contents from s3 too short to be real",
    )
