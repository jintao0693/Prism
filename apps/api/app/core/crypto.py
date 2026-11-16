"""敏感字段加解密（API Key 等）。"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def _fernet() -> Fernet:
    """用 SECRET_KEY 派生 Fernet 密钥。"""
    settings = get_settings()
    digest = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(plain: str) -> str:
    """加密明文密钥。"""
    if not plain:
        return ""
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    """解密；失败返回空串。"""
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return ""


def mask_secret(plain: str) -> str:
    """脱敏展示：仅保留末 4 位。"""
    if not plain:
        return ""
    if len(plain) <= 4:
        return "****"
    return "*" * (len(plain) - 4) + plain[-4:]
