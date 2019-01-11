import subprocess
import boto3
import sys
from botocore.exceptions import ClientError


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class BackupContext:
    def __init__(self, ssm_path=None):
        if ssm_path is None:
            raise Exception("BackupContext needs ssm_path")
        self.ssm_path = ssm_path
        self.ssm = boto3.client("ssm")

        self.ssm_paramdef = dict(Name=ssm_path + "/s3_base")

    def s3_target_url(self):
        try:
            s3_base = self.ssm.get_parameter(**self.ssm_paramdef)["Parameter"]["Value"]
        except ClientError as e:
            eprint("Failed to get parameter: " + self.ssm_paramdef["Name"])
            raise e
        return s3_base + "/backup"

    def run(self, command=None):
        s3_target = self.s3_target_url()
        enc_env = {
            "BACKUP_CONTEXT_S3_TARGET": s3_target,
            "BACKUP_CONTEXT_ENCRYPT_COMMAND": "backup_encrypt",
        }
        subprocess.run([command], env=enc_env)
