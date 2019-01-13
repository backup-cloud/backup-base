from __future__ import annotations
import subprocess
import boto3  # type: ignore
import os
import sys
import gpg  # type: ignore
from tempfile import TemporaryDirectory
from botocore.exceptions import ClientError  # type: ignore
from typing import Dict, List


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class BackupContext:
    # TODO - recipients should either come from S3 keys or from SSM
    def __init__(self, ssm_path: str, recipients: List[str], bindir: str = None):
        if bindir is None:
            bindir = os.getcwd() + "/bin"
        if not os.path.exists(bindir):
            os.makedirs(bindir)
        self.bindir = bindir
        self.ssm_path = ssm_path
        self.ssm = boto3.client("ssm")
        self.recipients = recipients

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
        key_path = self.s3_path() + "/config/public-keys/test-key.pub"
        obj = bucket.Object(key_path)
        try:
            gpg_key = obj.get()["Body"].read()
        except ClientError as e:
            eprint("Failed to get public key: " + key_path)
            raise e

        assert len(gpg_key) > 64, (
            "public key: "
            + key_path
            + " is corrupt - too short at "
            + str(len(gpg_key))
            + " characters"
        )

        gpg_context.key_import(gpg_key)

    def setup_encrypt_command(self):
        c = gpg.Context(armor=True)
        self.gpgdir = TemporaryDirectory()
        c.home_dir = self.gpgdir.name
        self.get_gpg_keys(c)
        self.gpg_context = c

        script = """\
#!/bin/sh
set -evx
gpg --batch --homedir "{HOMEDIR}" --recipient "{KEYID}" --encrypt --trust-model always $1
""".format(
            HOMEDIR=self.gpgdir.name, KEYID=self.recipients[0]
        )

        prog_path = self.bindir + "/backup_encrypt"
        with open(prog_path, "w") as script_file:
            script_file.write(script)
        subprocess.call(["chmod", "a+x", prog_path])

    def run(self, command: List[str]):
        self.setup_encrypt_command()
        s3_target = self.s3_target_url()
        enc_env: Dict[str, str] = {
            "BACKUP_CONTEXT_S3_TARGET": s3_target,
            "BACKUP_CONTEXT_ENCRYPT_COMMAND": "backup_encrypt",
            "PATH": self.bindir + ":" + os.environ["PATH"],
        }
        cp = subprocess.run(command, env=enc_env)
        cp.check_returncode()
