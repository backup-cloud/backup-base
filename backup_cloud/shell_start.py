import argparse
import sys
from backup_cloud import BackupContext


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def main():
    parser = argparse.ArgumentParser(
        description="Preparation and definitions for encrypted backups."
    )
    parser.add_argument("ssm_path", help="path for finding backup configuration in ssm")

    args = parser.parse_args()

    bc = BackupContext(ssm_path=args.ssm_path, clean=False)
    (encrypt_script, upload_script) = bc.setup_commands()

    set_shell_vars(encrypt_script, upload_script, bc.s3_target_url())


def upload_main():
    parser = argparse.ArgumentParser(description="Upload files to S3 bucket.")
    parser.add_argument("ssm_path", help="path for finding backup configuration in ssm")
    parser.add_argument("source_dir", help="file or directory to upload")
    parser.add_argument("dest_s3_path", help="s3 path to upload to")

    args = parser.parse_args()

    bc = BackupContext(ssm_path=args.ssm_path, clean=False)
    (encrypt_script, upload_script) = bc.setup_commands()

    eprint("starting upload of " + args.source_dir + " to " + args.dest_s3_path + "\n")

    bc.upload_path(args.source_dir, args.dest_s3_path)


def set_shell_vars(encrypt_script, upload_script, target_url):
    """output commands that shell can use to set variables

    this should be used something like

        eval $(start_backup_context "$SSM_PATH")

    and will then set the variables in the shell needed to use the
    backup script.

    Here be little dragons.  This output is designed to be evaluated
    by eval but might be put through quoting or not.  Probably we
    don't have to pass anything complicated but if we end up putting
    encryption keys through it might get nasty.  Not yet explicitly
    stating it but we assume we are called as something like

      1) eval $(start_backup_context "$SSM_PATH")
    or
      2) VAR="$(start_backup_context "$SSM_PATH")"
         eval $VAR

    ideally we should also support

       3) eval `start_backup_context "$SSM_PATH"`
    and
       4) eval "$(start_backup_context "$SSM_PATH")"

    but that might break if we ever have to include a backslash '\' to
    quote something so prefer the $() form when using.

    due to existing usage priority for supporting shells should be
     1) bash
     2) dash
     3) ash (other)
     4) zsh
     5) other sh compatible

    """

    print("export BACKUP_CONTEXT_ENCRYPT_COMMAND=" + encrypt_script + ";\n")
    print("export BACKUP_CONTEXT_UPLOAD_COMMAND=" + upload_script + ";\n")
    print("export BACKUP_CONTEXT_S3_TARGET=" + target_url + ";\n")
    print("echo configured backup context;\n")
