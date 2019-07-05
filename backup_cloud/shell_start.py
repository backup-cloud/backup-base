import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Preparation and definitions for encrypted backups."
    )
    parser.add_argument("ssm_path", help="path for finding backup configuration in ssm")

    args = parser.parse_args()
    from backup_cloud import BackupContext

    bc = BackupContext(ssm_path=args.ssm_path, clean=False)
    script = bc.setup_encrypt_command()

    # Here be little dragons.  This output is designed to be evaluated
    # by eval but might be put through quoting or not.  Probably we
    # don't have to pass anything complicated but if we end up putting
    # encryption keys through it might get nasty.  Not yet explicitly
    # stating it but we assume we are called as something like

    #   1) eval $(start_backup_context "$SSM_PATH")
    # or
    #   2) VAR="$(start_backup_context "$SSM_PATH")"
    #      eval $VAR

    # ideally we should also support

    #    3) eval `start_backup_context "$SSM_PATH"`
    # and
    #    4) eval "$(start_backup_context "$SSM_PATH")"

    # but that might break if we ever have to include a backslash '\' to
    # quote something so prefer the $() form when using.

    # due to existing usage priority for supporting shells should be
    #  1) bash
    #  2) dash
    #  3) ash (other)
    #  4) zsh
    #  5) other sh compatible

    print("export BACKUP_CONTEXT_ENCRYPT_COMMAND=" + script + ";\n")
    print("export BACKUP_CONTEXT_S3_TARGET=" + bc.s3_target_url() + ";\n")
    print("echo configured backup context;\n")
    pass
