from os import environ
import sys
from subprocess import run
import gpg
from tempfile import TemporaryDirectory
import random
import string
import boto3
from dotenv import load_dotenv
from hamcrest import assert_that, greater_than
from backup_context import ensure_s3_paths_in_ssm
from typeguard import typechecked  # type: ignore
from typing import List


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


@typechecked(always=True)
def call_ansible_step(
    step_name: str, playbook: str = "test-system.yml", extra_vars: List[str] = None
):
    """call_ansible_step - run a step by running a matching ansible tag"""

    proc_res = run(
        args=["ansible-playbook", "--list-tags", playbook], capture_output=True
    )
    if proc_res.returncode > 0:
        eprint(
            "Ansible STDOUT:\n", proc_res.stdout, "Ansible STDERR:\n", proc_res.stderr
        )
        raise Exception("ansible failed while listing tags")

    lines = [x.lstrip() for x in proc_res.stdout.split(b"\n")]
    steps_lists = [
        x[10:].rstrip(b"]").lstrip(b"[ ").split(b",")
        for x in lines
        if x.startswith(b"TASK TAGS:")
    ]
    steps = [x.lstrip() for y in steps_lists for x in y]
    eprint(b"\n".join([bytes(x) for x in steps]))
    if bytes(step_name, "latin-1") not in steps:
        raise Exception(
            "Ansible playbook: `" + playbook + "' missing tag: `" + step_name + "'"
        )

    eprint("calling ansible with: ", step_name)
    ansible_args = ["ansible-playbook", "-vvv", "--tags", step_name, playbook]
    if extra_vars is not None:
        ansible_args.extend(["--extra-vars", extra_vars])
    proc_res = run(args=ansible_args, capture_output=True)
    eprint("Ansible STDOUT:\n", proc_res.stdout, "Ansible STDERR:\n", proc_res.stderr)
    if proc_res.returncode > 0:
        raise Exception("ansible failed")


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
@given(u"I have a private public key pair")
def step_impl(context) -> None:

    c = gpg.Context(armor=True)

    context.gpgdir = TemporaryDirectory()
    c.home_dir = context.gpgdir.name
    userid = context.gpg_userid = "backup-" + "".join(
        [random.choice(string.ascii_letters + string.digits) for n in range(10)]
    )

    context.gpg_userlist = [userid]

    c.create_key(userid, algorithm="rsa3072", expires_in=31536000, encrypt=True)

    context.gpg_context = c
    context.public_key = c.key_export_minimal(pattern=userid)
    context.private_key = c.key_export_secret(pattern=userid)


@typechecked(always=True)
@given(u"the public key from that key pair is stored in an s3 bucket")
def step_impl(context) -> None:
    # Envfile is created when the S3 bucket is set up with credentials
    # that have access to the bucket.
    env_path = "./aws_credentials.env"
    load_dotenv(dotenv_path=env_path)

    # test_key is used for long lived resources like s3 buckets that
    # cannot be created for each test run.

    with open(".anslk_random_testkey") as f:
        test_key = f.read().rstrip()

    # by contrast random_test_prefix is used for resource local to
    # this test like an S3 path that can be created and destroyed
    # quickly - this will allow parallel testing and independence

    context.random_test_prefix = "".join(
        [random.choice(string.ascii_letters + string.digits) for n in range(10)]
    )

    context.s3_test_path = context.random_test_prefix

    s3 = boto3.resource("s3")
    bucket_name = environ["S3_TEST_BUCKET"]
    bucket = s3.Bucket(bucket_name)

    # s3_key = "config/public-keys" + test_key + "example.com.pub"
    s3_key = context.s3_test_path + "/config/public-keys/test-key.pub"

    assert_that(len(context.public_key), greater_than(64), "characters")
    bucket.put_object(Key=s3_key, Body=context.public_key)

    context.s3resource = s3
    context.test_key = test_key
    context.backup_bucket = bucket
    # use the same bucket for now for simplicity
    context.store_bucket = bucket


@typechecked(always=True)
@given(u"that I have configured a public key and a reference to it")
def step_impl(context) -> None:
    context.execute_steps(
        u"""
          given I have an S3 bucket for backup testing
            and I have a private public key pair
            and that private public key pair is stored in the bucket
        """
    )


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
@when(u"I run my backup container giving the base path")
def step_impl(context) -> None:
    raise NotImplementedError(
        u"STEP: When I run my backup container giving the base path"
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
