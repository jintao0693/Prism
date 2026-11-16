"""鉴权与密钥：JWT、密码哈希。"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    """
    对明文密码做哈希。
    使用随机 salt（写入哈希串），不依赖 SECRET_KEY，避免改密钥后演示账号失效。
    格式：pbkdf2_sha256$<salt_hex>$<digest_hex>
    """
    salt_bytes = salt if salt is not None else secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        120_000,
    )
    return f"pbkdf2_sha256${salt_bytes.hex()}${dk.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文与哈希是否匹配（兼容旧版：salt=SECRET_KEY 的双段格式）。"""
    if not hashed.startswith("pbkdf2_sha256$"):
        return False
    parts = hashed.split("$")
    if len(parts) == 3:
        _, salt_hex, _digest = parts
        try:
            salt = bytes.fromhex(salt_hex)
        except ValueError:
            return False
        return hmac.compare_digest(hash_password(plain, salt=salt), hashed)

    # 旧格式：pbkdf2_sha256$<digest>，salt 曾用 SECRET_KEY
    if len(parts) == 2:
        settings = get_settings()
        legacy = hashlib.pbkdf2_hmac(
            "sha256",
            plain.encode("utf-8"),
            settings.secret_key.encode("utf-8"),
            120_000,
        )
        return hmac.compare_digest(hashed, "pbkdf2_sha256$" + legacy.hex())

    return False


def create_access_token(
    subject: str,
    *,
    tenant_id: str,
    role: str,
    extra: dict[str, Any] | None = None,
) -> str:
    """签发访问令牌。claims 含 sub / tenant_id / role。"""
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes,
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "tenant_id": tenant_id,
        "role": role,
        "exp": expire,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """解析并校验 JWT；失败抛 JWTError。"""
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def try_decode_access_token(token: str) -> dict[str, Any] | None:
    """解析 JWT，失败返回 None。"""
    try:
        return decode_access_token(token)
    except JWTError:
        return None
