from backup_context import BackupContext
import boto3
from botocore.exceptions import ClientError  # type: ignore
import sys
from threading import Thread
import os


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def _download_worker(backup_context, bucket: str, path: str, dest_stream):
    # don't share resource with main thread for safety
    s3 = boto3.resource("s3")
    obj = s3.Object(bucket, path)
    src_stream = obj.get()["Body"]
    read_so_far: int = 0
    while True:
        chunk = src_stream.read(4096)
        if not chunk:
            break
        read_so_far += len(chunk)
        eprint("read " + str(read_so_far) + " bytes so far\n")
        dest_stream.write(chunk)


def _encrypt_worker(backup_context, source_stream, encrypted_stream):
    backup_context.encrypt(source_stream, sink=encrypted_stream)


def _encrypt_worker_debug(backup_context, source_stream, encrypted_stream):
    plaintext = source_stream.read()
    eprint("read plaintext: " + str(len(plaintext)) + " bytes\n")
    ciphertext, result, sign_result = backup_context.encrypt(plaintext)
    encrypted_stream.write(ciphertext)


def backup_s3_to_s3(
    backup_context: BackupContext,
    src_bucket: str,
    src_path: str,
    dest_bucket: str,
    dest_path: str,
):
    """backup a single S3 object

    Take a single S3 object, download it, encrypt it and reupload it
    into another S3 object.
    """

    (r_download, w_download) = os.pipe()
    (r_encrypt, w_encrypt) = os.pipe()

    r_download_file = os.fdopen(r_download, mode="rb")
    w_download_file = os.fdopen(w_download, mode="wb")
    r_encrypt_file = os.fdopen(r_encrypt, mode="rb")
    w_encrypt_file = os.fdopen(w_encrypt, mode="wb")

    t1 = Thread(
        target=_download_worker,
        args=(backup_context, src_bucket, src_path, w_download_file),
        daemon=True,
    )
    t1.start()
    t2 = Thread(
        target=_encrypt_worker_debug,
        args=(backup_context, r_download_file, w_encrypt_file),
        daemon=True,
    )
    t2.start()

    s3 = boto3.resource("s3")
    dest_obj = s3.Object(dest_bucket, dest_path)

    try:
        dest_obj.put({"Body": r_encrypt_file})
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
