import pytest

from app.core.errors import ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    get_password_hash,
    hash_refresh_token,
    validate_password_strength,
    verify_password,
)


def test_password_hashing():
    pw = "SuperSecureP@ss123"
    hashed = get_password_hash(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_password_strength_validation():
    with pytest.raises(ValidationError):
        validate_password_strength("short12")
    
    # Should not raise for 10+ chars
    validate_password_strength("1234567890")

def test_jwt_access_token_cycle():
    data = {"sub": "user-1234-abcd"}
    token = create_access_token(data)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "user-1234-abcd"
    assert decoded["type"] == "access"

def test_refresh_token_hashing():
    token = create_refresh_token()
    assert len(token) > 20
    h1 = hash_refresh_token(token)
    h2 = hash_refresh_token(token)
    assert h1 == h2
    assert len(h1) == 64
