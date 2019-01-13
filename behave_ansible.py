from typeguard import typechecked  # type: ignore
from subprocess import run
from typing import List
import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


@typechecked(always=True)
def call_ansible_step(
    step_name: str, playbook: str = "test-system.yml", extra_vars: List[str] = None
):
    """call_ansible_step - run a step by running a matching ansible tag"""

    proc_res = run(
        args=["ansible-playbook", "--list-tags", playbook], capture_output=True
    )
    if proc_res.returncode > 0:
        eprint(
            "Ansible STDOUT:\n", proc_res.stdout, "Ansible STDERR:\n", proc_res.stderr
        )
        raise Exception("ansible failed while listing tags")

    lines = [x.lstrip() for x in proc_res.stdout.split(b"\n")]
    steps_lists = [
        x[10:].rstrip(b"]").lstrip(b"[ ").split(b",")
        for x in lines
        if x.startswith(b"TASK TAGS:")
    ]
    steps = [x.lstrip() for y in steps_lists for x in y]
    eprint(b"\n".join([bytes(x) for x in steps]))
    if bytes(step_name, "latin-1") not in steps:
        raise Exception(
            "Ansible playbook: `" + playbook + "' missing tag: `" + step_name + "'"
        )

    eprint("calling ansible with: ", step_name)
    ansible_args = ["ansible-playbook", "-vvv", "--tags", step_name, playbook]
    if extra_vars is not None:
        ansible_args.extend(["--extra-vars", extra_vars])
    proc_res = run(args=ansible_args, capture_output=True)
    eprint("Ansible STDOUT:\n", proc_res.stdout, "Ansible STDERR:\n", proc_res.stderr)
    if proc_res.returncode > 0:
        raise Exception("ansible failed")
