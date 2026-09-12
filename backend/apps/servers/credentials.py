import base64
import hashlib

from django.conf import settings


class CredentialUnavailable(RuntimeError):
    """Raised when the optional encryption dependency is not installed."""


def _fernet():
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise CredentialUnavailable("Install the cryptography dependency to store SSH passwords securely.") from exc
    seed = hashlib.sha256(str(settings.SECRET_KEY).encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(seed))


def encrypt_password(password):
    if not password:
        return ""
    return _fernet().encrypt(str(password).encode("utf-8")).decode("ascii")


def decrypt_password(value):
    if not value:
        return ""
    return _fernet().decrypt(str(value).encode("ascii")).decode("utf-8")
