import subprocess
from subprocess import CompletedProcess
import boto3  # type: ignore
import os
import sys
import gpg  # type: ignore
from tempfile import TemporaryDirectory, mkdtemp, NamedTemporaryFile
from botocore.exceptions import ClientError  # type: ignore
from typing import Dict, List, Generator, Tuple
from threading import Thread


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def _encrypt_worker(backup_context, source_stream, encrypted_stream):
    backup_context.encrypt(source_stream, sink=encrypted_stream)
    try:
        encrypted_stream.flush()
    except BrokenPipeError as e:
        eprint("BrokenPipeError at end of encrypted stream;")
        raise e
    encrypted_stream.close()


def _encrypt_worker_debug(backup_context, source_stream, encrypted_stream):
    plaintext = source_stream.read()
    eprint("read plaintext: " + str(len(plaintext)) + " bytes\n")
    ciphertext, result, sign_result = backup_context.encrypt(plaintext)
    encrypted_stream.write(ciphertext)
    try:
        encrypted_stream.flush()
    except BrokenPipeError as e:
        eprint("BrokenPipeError at end of encrypted stream;")
        raise e
    encrypted_stream.close()


class BackupContext:
    """provide a context which will allow us to easily run backups and encrypt them
    ssm_path: path in SSM to find configuration parameters
    recipients: specific list of gpg recipients to encrypted to.
    bindir: directory in create scripts used for encryption etc.
    no_clean: don't delete GPG data directory when garbage collected (useful for scripts)
    """

    def __init__(
        self,
        ssm_path: str = "/backup_cloud/base_defs",
        recipients: List[str] = None,
        bindir: str = None,
        clean: bool = True,
    ):
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
        if clean:
            self._gpgdir = TemporaryDirectory()
            self.dirname = self._gpgdir.name
        else:
            self.dirname = mkdtemp()
        c.home_dir = self.dirname
        self.get_gpg_keys(c)
        self.gpg_context = c

    def get_recipients(self):
        """return the recipients we should encrypt to

        normally returns the recipients requested during startup or
        all of the recipients in all known private keys if none were
        specified.
        """
        if self.recipients is None:
            return self.all_recipients
        else:
            return self.recipients

    def s3_path(self) -> str:
        """return the base path in S3 where we should work - read from SSM
        """
        ssm_path: str = self.ssm_path
        ssm_paramdef = dict(Name=ssm_path + "/s3_path")
        try:
            s3_path = self.ssm.get_parameter(**ssm_paramdef)["Parameter"]["Value"]
            if s3_path.startswith("/"):
                s3_path = s3_path[1:]
        except ClientError as e:
            eprint("Failed to get parameter: " + ssm_paramdef["Name"])
            raise e
        return s3_path

    # here we can't easily and safely do type annotations due to
    # Boto3's dynamic code.  Potentially see the
    # boto3-type-annotations module however.
    def s3_bucket(self):
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

    def s3_target_url(self) -> str:
        s3path = self.s3_path()
        if s3path.endswith("/") or not s3path:
            full_path = self.s3_path() + "backup"
        else:
            full_path = s3path + "/backup"
        return full_path

    def _s3_key_url(self) -> str:
        s3path = self.s3_path()
        if s3path.endswith("/"):
            full_path = s3path + "config/public-keys/"
        else:
            full_path = s3path + "/config/public-keys/"
        return full_path

    def download_gpg_keys(self) -> Generator[bytes, None, None]:
        bucket = self.s3_bucket()

        if self.s3_path().endswith("/") or not self.s3_path():
            folder_path = self.s3_path() + "config/public-keys/"
        else:
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

            yield (gpg_key)

    def get_gpg_keys(self, gpg_context) -> None:
        """recover gpg keys from config/public-keys folder in S3

        we pick up all the keys from the folder and then import them to the gpg
        context which makes them available for encrypting.

        N.B. it is the responsibility of those loading keys into the bucket to
        ensure that a) the keys are trusted ones that belong to their owners and
        b) they are correctly labelled for use as recipients.

        """

        for gpg_key in self.download_gpg_keys():
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
        recipient_keys = [c.get_key(k) for k in self.get_recipients()]
        options = dict(recipients=recipient_keys, sign=False, always_trust=True)
        options.update(kwargs)

        return c.encrypt(plaintext, *args, **options)

    def create_script(self, script: str) -> str:
        script_file = NamedTemporaryFile(delete=False)
        script_file.write(script.encode("utf-8"))
        script_file.close()
        subprocess.call(["chmod", "a+x", script_file.name])
        return script_file.name

    def setup_commands(self) -> Tuple[str, str]:
        """prepare a command that can be used in scripts for encrypting data

        this will be done for you automatically if you use the
        backup_context.run() - we create a command backup_encrypt
        which will run the encryption for you.
        """

        recipients = self.get_recipients()

        if len(recipients) < 1:
            raise Exception(
                "No recipients found - need to have at least one public key configured"
            )

        rcpt_clause = (
            '--recipient "' + '" --recipient "'.join([str(x) for x in recipients]) + '"'
        )

        encrypt_script = """\
#!/bin/sh
set -evx
if [[ ! -e $1 ]]
then
        echo "file $1 doesn't exist to encrypt - aborting" >&2
        exit 6
fi
if [[ ! -f $1 ]]
then
        echo "file $1 is not a plain file we can encrypt - aborting" >&2
        exit 6
fi
rm -f $1.gpg
gpg --batch --homedir "{HOMEDIR}" {RCPTS} --encrypt --trust-model always $1
""".format(
            HOMEDIR=self.dirname, RCPTS=rcpt_clause
        )

        self.encrypt_script_path = self.create_script(encrypt_script)
        upload_script = """\
#!/bin/sh
set -evx
if [[ ! -e "$1" ]]
then
        echo "file $1 doesn't exist to upload - aborting" >&2
        exit 6
fi
if [[ "$1" == "" ]]
then
        echo "missing argument - backup-cloud-upload requires source_directory and dest_s3_path"
        exit 6
fi
backup-cloud-upload {SSM_PATH} $1 $2
""".format(
            SSM_PATH=self.ssm_path
        )

        self.upload_script_path = self.create_script(upload_script)

        return self.encrypt_script_path, self.upload_script_path

    def run(self, command: List[str]) -> CompletedProcess:
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

        script, _ = self.setup_commands()
        s3_target = self.s3_target_url()
        enc_env: Dict[str, str] = {
            "BACKUP_CONTEXT_S3_TARGET": s3_target,
            "BACKUP_CONTEXT_ENCRYPT_COMMAND": script,
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

    def upload_path(self, src_directory, dest_s3_path):
        """upload a directory to s3 encrypting the individual file(s)
        as we go.

        In order to have a reliable secure backup many backup systems
        dump multiple files in a directory structure.  E.g. git backup
        systems dump each repository into a separate directory.   This
        function uploads these files as is but encrypts each
        individual file.

        N.B. if the names of the files themselves may be a problem if
        leaked this can be a non-appropriate solution.  E.g. having
        "list-of-spectra-secret-agenta.sql.gpg" will almost certainly
        mean James Bond will force you to talk.

        On the other hand, the file "customer-addresses.sql.gpg" will
        just give away that you have customers and that you have lots
        of them.  Provided that the encryption is done correctly you
        will not end up leaing your customer's personal information,
        which solves a major commercial problem.

        """
        if not os.path.isdir(src_directory):
            raise Exception("upload_path() can only handle directories right now!")

        basepath, target_dirname = os.path.split(src_directory)

        for subdir, dirs, files in os.walk(src_directory):
            for file in files:
                src_name = os.path.join(subdir, file)
                rel = os.path.relpath(subdir, basepath)
                dest_name = (
                    self.s3_path() + "/backup/" + dest_s3_path + "/" + rel + "/" + file
                )

                self.backup_file_to_s3(src_name, self.s3_bucket(), dest_name)

    def backup_file_to_s3(self, src_file: str, dest_bucket, dest_path: str):
        """backup a single file to S3

        Take a single file encrypt it and upload it into an S3 object.
        """

        eprint(
            "uploading "
            + src_file
            + " to bucket "
            + dest_bucket.name
            + " with path "
            + dest_path
            + "\n"
        )

        (r_encrypt, w_encrypt) = os.pipe()

        with open(src_file, "rb") as f:
            r_encrypt_file = os.fdopen(r_encrypt, mode="rb")
            w_encrypt_file = os.fdopen(w_encrypt, mode="wb")

            encrypt_thread = Thread(
                target=_encrypt_worker_debug,
                args=(self, f, w_encrypt_file),
                daemon=True,
            )
            encrypt_thread.start()

            dest_obj = dest_bucket.Object(dest_path)

            def callback(x):
                eprint("uploaded " + str(x) + " bytes")

            try:
                dest_obj.upload_fileobj(r_encrypt_file, Callback=callback)
            except ClientError as e:
                eprint(
                    "Failed to store: ",
                    src_file,
                    " in: ",
                    dest_bucket,
                    "/",
                    dest_path,
                    " aborting.\n",
                )
                raise e
