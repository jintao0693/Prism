"""鉴权与密钥：JWT、密码哈希。"""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    """
    对明文密码做哈希。
    演示环境使用 PBKDF2，避免 Windows 下 bcrypt 后端兼容问题；
    生产可替换为 argon2 / bcrypt。
    """
    settings = get_settings()
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        settings.secret_key.encode("utf-8"),
        120_000,
    )
    return "pbkdf2_sha256$" + dk.hex()


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文与哈希是否匹配。"""
    if not hashed.startswith("pbkdf2_sha256$"):
        return False
    return hmac.compare_digest(hash_password(plain), hashed)


def create_access_token(
    subject: str,
    *,
    tenant_id: str,
    role: str,
    extra: dict[str, Any] | None = None,
) -> str:
    """签发访问令牌。claims 含 sub / tenant_id / role。"""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
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
