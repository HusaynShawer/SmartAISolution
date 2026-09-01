def test_hash_and_verify_password():
    from core.security import hash_password, verify_password

    hashed = hash_password("s3cret")
    assert hashed != "s3cret"
    assert verify_password("s3cret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_access_token():
    from core.security import create_access_token, decode_access_token

    token = create_access_token({"sub": "user-1", "email": "a@b.com"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-1"
    assert payload["email"] == "a@b.com"


def test_decode_invalid_token_returns_none():
    from core.security import decode_access_token

    assert decode_access_token("not.a.valid-token") is None