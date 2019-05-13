from backup_cloud.base import BackupContext
from unittest.mock import patch


def test_handle_paths_with_and_without_slashes():
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
                    c.download_gpg_keys()
                    assert mockbucket.objects.filter.called_with(
                        Prefix="/unit/test/fake/s3/path/with/slash/config/public-keys/"
                    )

            with patch.object(
                c, "s3_path", return_value="/unit/test/fake/s3/path/without/slash"
            ):
                target = c.s3_target_url()
                assert "//" not in target
                assert target == "/unit/test/fake/s3/path/without/slash/backup"
                with patch.object(c, "s3_bucket") as mockbucket:
                    c.download_gpg_keys()
                    assert mockbucket.objects.filter.called_with(
                        Prefix="/unit/test/fake/s3/path/with/slash/config/public-keys/"
                    )
