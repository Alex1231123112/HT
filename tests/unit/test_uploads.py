from admin.api.routers.uploads import _safe_extension


def test_safe_extension_from_filename():
    assert _safe_extension("photo.jpg") == ".jpg"
    assert _safe_extension("doc.PDF") == ".pdf"
    assert _safe_extension("file.mp4") == ".mp4"


def test_safe_extension_no_extension():
    assert _safe_extension("noext") == ".bin"
    assert _safe_extension(None) == ".bin"


def test_safe_extension_long_extension_gets_bin():
    assert _safe_extension("file.abcdefghijk") == ".bin"
