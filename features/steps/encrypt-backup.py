import sys
import gpg
from tempfile import TemporaryDirectory
import random
import string
from hamcrest import assert_that, greater_than
from typeguard import typechecked  # type: ignore
from botocore.exceptions import ClientError
from typing import Any

given: Any
when: Any
then: Any


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

    # ubuntu bionic doesn't ahve key_export_minimial() so we fallback
    # in real life we can assume that the users would export using
    # some graphical tool.
    try:
        context.public_key = c.key_export_minimal(pattern=userid)
    except AttributeError:
        context.public_key = c.key_export(pattern=userid)

    context.private_key = c.key_export_secret(pattern=userid)


@typechecked(always=True)
@given(u"the public key from that key pair is stored in an s3 bucket")
def step_impl_1(context) -> None:

    # by contrast random_test_prefix is used for resource local to
    # this test like an S3 path that can be created and destroyed
    # quickly - this will allow parallel testing and independence

    context.random_test_prefix = "".join(
        [random.choice(string.ascii_letters + string.digits) for n in range(10)]
    )

    context.s3_test_path = context.random_test_prefix

    # s3_key = "config/public-keys" + testdir_random_id + "example.com.pub"
    context.s3_key = context.s3_test_path + "/config/public-keys/test-key.pub"

    assert_that(len(context.public_key), greater_than(64), "characters")
    try:
        context.backup_bucket.put_object(Key=context.s3_key, Body=context.public_key)
    except ClientError as e:
        eprint("failed to put public key into s3 bucket: " + context.bucket_name)
        raise e


@typechecked(always=True)
@given(u"that I have configured a public key and a reference to it")
def step_impl_2(context) -> None:
    context.execute_steps(
        u"""
          given I have an S3 bucket for backup testing
            and I have a private public key pair
            and that private public key pair is stored in the bucket
        """
    )


@typechecked(always=True)
@when(u"I run my backup container giving the base path")
def step_impl_3(context) -> None:
    raise NotImplementedError(
        u"STEP: When I run my backup container giving the base path"
    )
