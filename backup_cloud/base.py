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
    """provide a context which will allow us to easily run backups and encrypt them
    ssm_path: path in SSM to find configuration parameters
    recipients: specific list of gpg recipients to encrypted to.
    bindir: directory in create scripts used for encryption etc.

    """

    def __init__(self, ssm_path: str, recipients: List[str] = None, bindir: str = None):
        if bindir is None:
            bindir = os.getcwd() + "/bin"
        if not os.path.exists(bindir):
            os.makedirs(bindir)
        self.bindir = bindir
        self.ssm_path = ssm_path
        self.ssm = boto3.client("ssm")

        # recipients are specific recipents we are told to encrypt only to
        self.recipients = recipients
        # by default we encrypt to all recipients we find in key files
        # in our bucket - gathered here.
        self.all_recipients: List[str] = []

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

        we pick up all the keys from the folder and then import them to the gpg
        context which makes them available for encrypting.

        N.B. it is the responsibility of those loading keys into the bucket to
        ensure that a) the keys are trusted ones that belong to their owners and
        b) they are correctly labelled for use as recipients.

        """

        bucket = self.s3_bucket()
        folder_path = self.s3_path() + "/config/public-keys/"

        for obj in bucket.objects.filter(Prefix=folder_path):
            if obj.key == folder_path:
                continue
            try:
                gpg_key = obj.get()["Body"].read()
            except ClientError:
                eprint(
                    "Failed to get public key: s3://"
                    + obj.bucket
                    + "/"
                    + obj.key
                    + "\nIgnoring file and continuing.\n"
                )
                continue

            if len(gpg_key) < 64:
                eprint(
                    "public key:  s3://"
                    + obj.bucket_name
                    + "/"
                    + obj.key
                    + " is corrupt - too short at "
                    + str(len(gpg_key))
                    + " characters"
                )

            gpg_context.key_import(gpg_key)

        for i in gpg_context.keylist():
            uid = i.uids[0].uid
            assert len(uid) > 3, "gpg key without reasonable uid found: " + repr(i)
            self.all_recipients.append(uid)

        if len(self.all_recipients) < 1:
            raise Exception(
                "No recipients found in keys - need to have at least one public key configured"
            )

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

        recipients = self.recipients
        if recipients is None:
            recipients = self.all_recipients

        if len(recipients) < 1:
            raise Exception(
                "No recipients found - need to have at least one public key configured"
            )

        rcpt_clause = (
            '--recipient "' + '" --recipient "'.join([str(x) for x in recipients]) + '"'
        )

        script = """\
#!/bin/sh
set -evx
rm -f $1.gpg
gpg --batch --homedir "{HOMEDIR}" {RCPTS} --encrypt --trust-model always $1
""".format(
            HOMEDIR=self.gpgdir.name, RCPTS=rcpt_clause
        )

        prog_path = self.bindir + "/backup_encrypt"
        with open(prog_path, "w") as script_file:
            script_file.write(script)
        subprocess.call(["chmod", "a+x", prog_path])

    def run(self, command: List[str]):
        """run a command with the appropriate encryption commands ready to use

        command: list of command arguments as given to subprocess.run()

        run() sets things up (see backup_context.run() ) and then runs
        your script with appropriate environmment variables set.  You
        can call

            $BACKUP_CONTEXT_ENCRYPT_COMMAND myfile

        from your shellscript and it will output the encrypted file as
        myfile.gpg Please do use the environment variable since we may
        in future add specific options and so using the command
        directly might stop working.

        The environment variable $BACKUP_CONTEXT_S3_TARGET will
        contain the base location in AWS where your result should be
        written.  You can use a command like:

           aws s3 cp myfile.gpg $BACKUP_CONTEXT_S3_TARGET/myfold/myfile.gpg

        To upload the resulting file.

        Command compatibility will be maintained for (at least) ash and bash.

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
        if not cp.returncode == 0:
            eprint(
                "******* ENCRYPT PROCESS FAILED *********.\n\nStdout:\n"
                + cp.stdout.decode("utf-8", "backslashreplace")
                + "\n\nStderr:\n"
                + cp.stderr.decode("utf-8", "backslashreplace")
                + "\n"
            )
            cp.check_returncode()
        return cp
