from backup_cloud.base import BackupContext, _encrypt_worker, _encrypt_worker_debug
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
    _streampush_worker(src_stream, dest_stream)


def _streampush_worker(src_stream, dest_stream):
    """push from one streamlike object to another

    This is designed to run in a separate thread and push from one
    streamlike object (only need to have a read() function) to
    another.

    This allows us to convert a streaming object from S3 into a pipe.
    """

    read_so_far: int = 0
    chunk: bytes
    for chunk in iter(lambda: src_stream.read(4096), b""):
        read_so_far += len(chunk)
        eprint("read " + str(read_so_far) + " bytes so far\n")
        dest_stream.write(chunk)
    try:
        dest_stream.flush()
    except BrokenPipeError as e:
        eprint("BrokenPipeError at end of plaintext stream; probably okay; ignoring")
        raise e
    dest_stream.close()


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
    debug = True
    if debug:
        target = _encrypt_worker_debug
    else:
        target = _encrypt_worker
    t2 = Thread(
        args=(backup_context, r_download_file, w_encrypt_file),
        target=target,
        daemon=True,
    )
    t2.start()

    s3 = boto3.resource("s3")
    dest_obj = s3.Object(dest_bucket, dest_path)

    def callback(x):
        eprint("uploaded " + str(x) + " bytes")

    try:
        dest_obj.upload_fileobj(r_encrypt_file, Callback=callback)
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
