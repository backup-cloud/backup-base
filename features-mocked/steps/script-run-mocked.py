from unittest.mock import patch, ANY
from hamcrest import assert_that, equal_to

"""
Pretending to run an outside script but actually mock it and then run
checks on the arguments given to the script.
"""


@when(u"I run a backup script from that context")
def step_impl(context):
    with patch("subprocess.run") as mockrun:
        context.result = context.bc.run("fakeprog")
        mockrun.assert_called_once_with(["fakeprog"], env=ANY)
        context.script_env = mockrun.call_args[1]["env"]


@then(u"my S3 URL should be configured")
def step_impl(context):
    assert_that(
        context.script_env["BACKUP_CONTEXT_S3_TARGET"],
        equal_to(context.s3_backup_target),
    )


@then(u"my encryption command should be configured")
def step_impl(context):
    assert_that(
        context.script_env["BACKUP_CONTEXT_ENCRYPT_COMMAND"], equal_to("backup_encrypt")
    )
