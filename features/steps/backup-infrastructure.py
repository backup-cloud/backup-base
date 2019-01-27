from dotenv import load_dotenv
import boto3
from os import environ


@given(u"I have access to an account for doing backups")
def step_impl(context):
    # Envfile is created when the S3 bucket is set up with credentials
    # that have access to the bucket.
    env_path = "./aws_credentials.env"
    load_dotenv(dotenv_path=env_path)

    # testdir_random_id is used for long lived resources like s3 buckets that
    # cannot be created for each test run.

    with open(".anslk_random_testkey") as f:
        testdir_random_id = f.read().rstrip()

    s3 = boto3.resource("s3")
    context.bucket_name = environ["S3_TEST_BUCKET"]
    assert len(context.bucket_name) > len("test-backup-") + 2, (
        "bucket name: " + context.bucket_name + " missing random key"
    )
    bucket = s3.Bucket(context.bucket_name)

    context.s3resource = s3
    context.testdir_random_id = testdir_random_id

    # bucket we are going to have backups into
    context.backup_bucket = bucket
    # bucket we are storing data that needs backed up

    context.store_bucket = bucket
