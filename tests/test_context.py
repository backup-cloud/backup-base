from backup_cloud.base import BackupContext
from unittest.mock import patch


def test_should_clean_up_double_slashes_from_target_url():
    with patch("backup_cloud.base.boto3"):
        with patch.object(BackupContext, "get_gpg_keys"):
            c = BackupContext(ssm_path="/unit/test/fakessm")
            with patch.object(
                c, "s3_path", return_value="/unit/test/fakes3/s3/path/with/slash/"
            ):
                target = c.s3_target_url()
                assert "//" not in target
                assert target == "/unit/test/fakes3/s3/path/with/slash/backup"
                with patch.object(c, "s3_bucket") as mockbucket:
                    list(c.download_gpg_keys())
                    mockbucket().objects.filter.assert_called_with(
                        Prefix="/unit/test/fakes3/s3/path/with/slash/config/public-keys/"
                    )


def test_should_maintain_a_single_slash_in_path():
    with patch("backup_cloud.base.boto3"):
        with patch.object(BackupContext, "get_gpg_keys"):
            c = BackupContext(ssm_path="/unit/test/fakessm")
            with patch.object(
                c, "s3_path", return_value="/unit/test/fakes3/s3/path/without/slash"
            ):
                target = c.s3_target_url()
                assert "//" not in target
                assert target == "/unit/test/fakes3/s3/path/without/slash/backup"
                with patch.object(c, "s3_bucket") as mockbucket:
                    list(c.download_gpg_keys())
                    mockbucket().objects.filter.assert_called_with(
                        Prefix="/unit/test/fakes3/s3/path/without/slash/config/public-keys/"
                    )


def test_upload_should_clean_slashes_in_paths_of_target_objects():
    with patch("backup_cloud.base.boto3"):
        with patch.object(BackupContext, "get_gpg_keys"):
            c = BackupContext(ssm_path="/unit/test/fake")
            with patch.object(
                c, "s3_path", return_value="/unit/test/fake/s3/path/without/slash"
            ):
                with patch.object(c, "s3_bucket") as mockbucket:
                    c.backup_file_to_s3(
                        "/etc/hosts", mockbucket, "/this//that/theother"
                    )
                    mockbucket.Object.assert_called_with("this/that/theother")
