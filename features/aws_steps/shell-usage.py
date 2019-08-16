import subprocess
from typing import Any
from tempfile import TemporaryDirectory, mkstemp
import os
import string
import random

given: Any
when: Any


@given(u"I have a shell script which calls the backup command and encrypts that file")
def step_impl_0(context):
    context.shell_script = "fixtures/start_context_and_encrypt.sh"


@given(
    u"I have an upload script which calls the backup command and uploads the directory"
)
def step_impl_1(context):
    context.shell_script = "fixtures/start_context_and_upload_dir.sh"


@when(u"I run that script")
def step_impl_2(context):
    subprocess.run([context.shell_script, context.ssm_path], timeout=30, check=True)


@given(u"I have a directory containing multiple files")
def step_impl_3(context):
    context.directory = TemporaryDirectory()
    context.directory_name = context.directory.name
    context.filecontents = filecontents = {}
    basepath, dirname = os.path.split(context.directory.name)
    for _i in range(5):
        (fd, path) = mkstemp(dir=context.directory.name)
        dirpath, filename = os.path.split(path)
        file = os.fdopen(fd, mode="wb")
        contents = "".join(
            [random.choice(string.ascii_letters + string.digits) for n in range(16)]
        ).encode("utf-8")
        filecontents[dirname + "/" + filename] = contents
        file.write(contents)
        file.close()


@when(u"I run the upload script giving it the directory name and an s3 subfolder")
def step_impl_4(context):
    sub_path = "directory-backup"
    subprocess.run(
        [context.shell_script, context.ssm_path, context.directory_name, sub_path],
        timeout=30,
        check=True,
    )
    s3_expect = {}
    fc = context.filecontents
    for key in fc:
        dest_key = context.s3_backup_target + "/" + sub_path + "/" + key
        s3_expect[dest_key] = fc[key]
    context.s3_expect_decrypted_files = s3_expect
