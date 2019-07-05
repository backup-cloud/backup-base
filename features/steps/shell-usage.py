import subprocess
from typing import Any

given: Any
when: Any


@given(
    u"that I have a shell script which calls the backup command and encrypts that file"
)
def step_impl(context):
    context.shell_script = "fixtures/start_context_and_encrypt.sh"


@when(u"I run that script")
def step_impl_1(context):
    subprocess.run([context.shell_script, context.ssm_path], timeout=10, check=True)
