import backup_cloud.s3
from unittest.mock import Mock, call
from threading import Thread


def test_download_worker_should_read_repeatedly_and_push_to_file():
    stream = Mock()
    stream.read.side_effect = [
        b"this",
        b"that",
        b"theother",
        b"",
        Exception("overran data"),
    ]

    outfile = open("/tmp/q", "bw")
    # outfile = tempfile.NamedTemporaryFile()
    filename = outfile.name

    t1 = Thread(
        target=backup_cloud.s3._streampush_worker, args=(stream, outfile), daemon=True
    )
    t1.start()
    t1.join()

    stream.read.assert_has_calls([call(4096), call(4096), call(4096), call(4096)])

    with open(filename, "rb") as f:
        contents = f.read()

    assert contents == b"thisthattheother"


# def test_encryptor_creates_different_file():
#     assert False, "not implmeented"
