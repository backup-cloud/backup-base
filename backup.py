#!/usr/bin/env python
import boto3


def main(s3=None):
    key = "pgc6piip5yhg9k3"
    if not s3:
        s3 = boto3.resource("s3")
    bucket_name = "test-backup-" + key
    bucket = s3.Bucket(bucket_name)
    bucket.put_object(Key="backup/s3/" + key, Body="junk")


if __name__ == "__main__":
    main()
