import subprocess
import boto3
import sys
import gpg
from tempfile import TemporaryDirectory
from botocore.exceptions import ClientError
from typing import Dict


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class BackupContext:
    def __init__(self, ssm_path: str = None):
        if ssm_path is None:
            raise Exception("BackupContext needs ssm_path")
        self.ssm_path = ssm_path
        self.ssm = boto3.client("ssm")

    def s3_path(self) -> str:
        ssm_path: str = self.ssm_path
        ssm_paramdef = dict(Name=ssm_path + "/s3_path")
        try:
            s3_path = self.ssm.get_parameter(**ssm_paramdef)["Parameter"]["Value"]
        except ClientError as e:
            eprint("Failed to get parameter: " + ssm_paramdef["Name"])
            raise e
        return s3_path

    def s3_bucket(self) -> str:
        ssm_path = self.ssm_path
        ssm_paramdef: Dict[str, str] = dict(Name=ssm_path + "/s3_bucket")
        try:
            s3_bucket_name = self.ssm.get_parameter(**ssm_paramdef)["Parameter"][
                "Value"
            ]
        except ClientError as e:
            eprint("Failed to get parameter: " + ssm_paramdef["Name"])
            raise e
        s3 = boto3.resource("s3")
        return s3.Bucket(s3_bucket_name)

    def s3_target_url(self):
        return self.s3_path() + "/backup"

    def get_gpg_keys(self, gpg_context):
        bucket = self.s3_bucket()
        obj = bucket.Object(self.s3_path() + "/config/public-keys/test-key.pub")
        gpg_key = obj.get()["Body"].read()
        gpg_context.key_import(gpg_key)

    def setup_encrypt_command(self):
        c = gpg.Context(armor=True)
        self.gpgdir = TemporaryDirectory()
        c.home_dir = self.gpgdir.name
        self.get_gpg_keys(c)
        self.gpg_context = c

        script = """\
#!/bin/sh
gpg --homedir "{}" --recipient "${KEYID}" --encrypt --trust-model always > "$THE_DUMP_FILE"
""".format(
            self.gpgdir.name
        )
        with open("/usr/bin/backup_encrypt", "w") as script_file:
            script_file.write(script)

    def run(self, command=None):
        self.setup_encrypt_command()
        s3_target = self.s3_target_url()
        enc_env: Dict[str, str] = {
            "BACKUP_CONTEXT_S3_TARGET": s3_target,
            "BACKUP_CONTEXT_ENCRYPT_COMMAND": "backup_encrypt",
        }
        cp = subprocess.run(command, env=enc_env)
        cp.check_returncode()
