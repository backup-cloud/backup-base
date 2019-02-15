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


def set_string_par(ssm, path: str, value: str) -> None:
    ssm_paramdef = dict(Name=path, Value=value, Type="String", Overwrite=True)
    eprint("putting: " + value + "into ssm param: " + path)
    ssm.put_parameter(**ssm_paramdef)


def ensure_s3_paths_in_ssm(ssm_path: str, s3_bucket: str, s3_path: str) -> None:
    ssm = boto3.client("ssm")
    set_string_par(ssm, ssm_path + "/s3_bucket", s3_bucket)
    set_string_par(ssm, ssm_path + "/s3_path", s3_path)


class BackupContext:
    # TODO - recipients should either come from S3 keys or from SSM
    """provide a context which will allow us to easily run backups and encrypt them
    """

    def __init__(self, ssm_path: str, recipients: List[str], bindir: str = None):
        if bindir is None:
            bindir = os.getcwd() + "/bin"
        if not os.path.exists(bindir):
            os.makedirs(bindir)
        self.bindir = bindir
        self.ssm_path = ssm_path
        self.ssm = boto3.client("ssm")
        self.recipients = recipients

        c = gpg.Context(armor=True)
        self.gpgdir = TemporaryDirectory()
        c.home_dir = self.gpgdir.name
        self.get_gpg_keys(c)
        self.gpg_context = c

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
        except (ClientError) as e:
            eprint("Failed to get parameter: " + ssm_paramdef["Name"])
            raise e
        s3 = boto3.resource("s3")
        return s3.Bucket(s3_bucket_name)

    def s3_target_url(self):
        return self.s3_path() + "/backup"

    def get_gpg_keys(self, gpg_context):
        """recover gpg keys from config/public-keys folder in S3

        we pick up all the keys from the folder and then import them
        to the gpg context which makes them available for encrypting.
        """

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

    def encrypt(self, plaintext, *args, **kwargs):
        """TODO: encrypt_stream - encrypt a stream into another stream

        Given a stream of plaintext data return a stream of encrypted
        data.  This looks very much like gpg.Context.encrypt except it
        provides defaults for recipients, sets always_trust True so
        our imported keys work and sign False since we don't have a
        key to sign from (yet?).
        """

        c = self.gpg_context
        recipient_keys = [c.get_key(k) for k in self.recipients]
        options = dict(recipients=recipient_keys, sign=False, always_trust=True)
        options.update(kwargs)

        return c.encrypt(plaintext, *args, **options)

    def setup_encrypt_command(self):
        """prepare a command that can be used in scripts for encrypting data

        this will be done for you automatically if you use the
        backup_context.run() - we create a command backup_encrypt
        which will run the encryption for you.
        """

        script = """\
#!/bin/sh
set -evx
rm -f $1.gpg
gpg --batch --homedir "{HOMEDIR}" --recipient "{KEYID}" --encrypt --trust-model always $1
""".format(
            HOMEDIR=self.gpgdir.name, KEYID=self.recipients[0]
        )

        prog_path = self.bindir + "/backup_encrypt"
        with open(prog_path, "w") as script_file:
            script_file.write(script)
        subprocess.call(["chmod", "a+x", prog_path])

    def run(self, command: List[str]):
        """run a command with the appropriate encryption commands ready to use


        this sets things up (see backup_context.run() ) and then runs
        your script with appropriate environmment variables set.  You can call

            $BACKUP_CONTEXT_ENCRYPT_COMMAND myfile

        from your shellscript and it will output the encrypted file as
        myfile.gpg Please do use the environment variable since we may
        in future add specific options and so using the command
        directly might stop working.

        command compatibility will be maintained for (at least) ash and bash.
        """

        self.setup_encrypt_command()
        s3_target = self.s3_target_url()
        enc_env: Dict[str, str] = {
            "BACKUP_CONTEXT_S3_TARGET": s3_target,
            "BACKUP_CONTEXT_ENCRYPT_COMMAND": "backup_encrypt",
            "PATH": self.bindir + ":" + os.environ["PATH"],
        }
        cp = subprocess.run(
            command, env=enc_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        cp.check_returncode()
        return cp
