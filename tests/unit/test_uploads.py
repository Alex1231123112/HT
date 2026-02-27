from admin.api.routers.uploads import _detect_file_type


def test_detect_jpeg_signature():
    payload = b"\xff\xd8\xff\xee" + b"0" * 20
    assert _detect_file_type(payload) == "image/jpeg"


def test_detect_png_signature():
    payload = b"\x89PNG\r\n\x1a\n" + b"0" * 20
    assert _detect_file_type(payload) == "image/png"


def test_detect_unsupported_signature():
    payload = b"random-bytes"
    assert _detect_file_type(payload) is None
