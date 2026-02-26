from admin.api.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    is_token_revoked,
    revoke_token,
    verify_password,
)


def test_password_hashing_roundtrip():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_jwt_roundtrip():
    token = create_access_token("admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "admin"


def test_token_revoke():
    token = create_access_token("admin")
    revoke_token(token)
    assert is_token_revoked(token) is True
