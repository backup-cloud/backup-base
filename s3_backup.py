from backup_context import BackupContext
import boto3
from botocore.exceptions import ClientError  # type: ignore
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def backup_s3_to_s3(
    backup_context: BackupContext,
    src_bucket: str,
    src_path: str,
    dest_bucket: str,
    dest_path: str,
):
    s3 = boto3.resource("s3")
    source_obj = s3.Object(src_bucket, src_path)
    dest_obj = s3.Object(dest_bucket, dest_path)

    source_stream = source_obj.get()["Body"]

    encrypted_stream = backup_context.encrypt_stream(source_stream)

    try:
        dest_obj.put({"Body": encrypted_stream})
    except ClientError as e:
        eprint(
            "Failed to store: ",
            src_bucket,
            "/",
            src_path,
            " in: ",
            dest_bucket,
            "/",
            dest_path,
            " aborting.\n",
        )
        raise e
