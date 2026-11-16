"""密码哈希：随机 salt，且不依赖 SECRET_KEY。"""

from __future__ import annotations

import os

from app.core.security import hash_password, verify_password


def test_hash_uses_random_salt() -> None:
    a = hash_password("prism123")
    b = hash_password("prism123")
    assert a != b
    assert verify_password("prism123", a)
    assert verify_password("prism123", b)
    assert not verify_password("wrong", a)


def test_hash_survives_secret_key_change() -> None:
    hashed = hash_password("prism123")
    os.environ["SECRET_KEY"] = "totally-different-key"
    # get_settings 可能已缓存；verify 新格式不读 SECRET_KEY
    assert verify_password("prism123", hashed)


def test_legacy_secret_key_salt_still_verifies() -> None:
    """旧格式 pbkdf2_sha256$<digest>（salt=SECRET_KEY）仍可校验。"""
    import hashlib

    from app.core.config import get_settings

    settings = get_settings()
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        b"prism123",
        settings.secret_key.encode("utf-8"),
        120_000,
    )
    legacy = "pbkdf2_sha256$" + dk.hex()
    assert verify_password("prism123", legacy)
    assert not verify_password("nope", legacy)
