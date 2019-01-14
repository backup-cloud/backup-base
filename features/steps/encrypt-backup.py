from os import environ
import sys
import gpg
from tempfile import TemporaryDirectory
import random
import string
import boto3
from dotenv import load_dotenv
from hamcrest import assert_that, greater_than
from typeguard import typechecked  # type: ignore


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


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

    # testdir_random_id is used for long lived resources like s3 buckets that
    # cannot be created for each test run.

    with open(".anslk_random_testkey") as f:
        testdir_random_id = f.read().rstrip()

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

    # s3_key = "config/public-keys" + testdir_random_id + "example.com.pub"
    s3_key = context.s3_test_path + "/config/public-keys/test-key.pub"

    assert_that(len(context.public_key), greater_than(64), "characters")
    bucket.put_object(Key=s3_key, Body=context.public_key)

    context.s3resource = s3
    context.testdir_random_id = testdir_random_id
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
@when(u"I run my backup container giving the base path")
def step_impl(context) -> None:
    raise NotImplementedError(
        u"STEP: When I run my backup container giving the base path"
    )
