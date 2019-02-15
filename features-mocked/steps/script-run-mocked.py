from unittest.mock import patch
from hamcrest import assert_that, equal_to, contains
from backup_cloud import BackupContext

# MIKED: oh the irony of the following line
from typeguard import typechecked  # type: ignore
from behave.runner import Context  # type: ignore

"""
Pretending to run an outside script but actually mock it and then run
checks on the arguments given to the script.
"""


@typechecked(always=True)
@when(u"I run a backup script from that context")  # type: ignore
def step_impl_run(context: Context) -> None:
    bc: BackupContext = context.backup_context
    with patch("subprocess.run") as mockrun:
        context.result = bc.run(["fakeprog"])
        assert_that(mockrun.call_args[0], contains(["fakeprog"]))
        context.script_env = mockrun.call_args[1]["env"]


@typechecked(always=True)
@then(u"my S3 URL should be configured")  # type: ignore
def step_impl_url(context: Context) -> None:
    assert_that(
        context.script_env["BACKUP_CONTEXT_S3_TARGET"],
        equal_to(context.s3_backup_target),
    )


@typechecked(always=True)
@then(u"my encryption command should be configured")  # type: ignore
def step_impl_encrypt(context: Context) -> None:
    assert_that(
        context.script_env["BACKUP_CONTEXT_ENCRYPT_COMMAND"], equal_to("backup_encrypt")
    )
