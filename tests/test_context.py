from backup_cloud.base import BackupContext
from unittest.mock import patch


def test_should_handle_paths_with_double_slashes_so_we_end_up_with_one_slash():
    with patch("backup_cloud.base.boto3"):
        with patch.object(BackupContext, "get_gpg_keys"):
            c = BackupContext(ssm_path="/unit/test/fake")
            with patch.object(
                c, "s3_path", return_value="/unit/test/fake/s3/path/with/slash/"
            ):
                target = c.s3_target_url()
                assert "//" not in target
                assert target == "/unit/test/fake/s3/path/with/slash/backup"
                with patch.object(c, "s3_bucket") as mockbucket:
                    list(c.download_gpg_keys())
                    assert mockbucket().objects.filter.assert_called_with(
                        Prefix="/unit/test/fake/s3/path/with/slash/config/public-keys/"
                    )


def test_should_handle_paths_with_single_slashes_so_we_end_up_with_one_slash():
    with patch("backup_cloud.base.boto3"):
        with patch.object(BackupContext, "get_gpg_keys"):
            c = BackupContext(ssm_path="/unit/test/fake")
            with patch.object(
                c, "s3_path", return_value="/unit/test/fake/s3/path/without/slash"
            ):
                target = c.s3_target_url()
                assert "//" not in target
                assert target == "/unit/test/fake/s3/path/without/slash/backup"
                with patch.object(c, "s3_bucket") as mockbucket:
                    list(c.download_gpg_keys())
                    assert mockbucket().objects.filter.assert_called_with(
                        Prefix="/unit/test/fake/s3/path/with/slash/config/public-keys/"
                    )
