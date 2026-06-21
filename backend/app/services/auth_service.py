import hmac

from passlib.context import CryptContext

from app.config import AUTH_PASSWORD, AUTH_USERNAME


_password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
_admin_password_hash = _password_context.hash(AUTH_PASSWORD)


def verify_credentials(username: str, password: str) -> bool:
    username_matches = hmac.compare_digest(username, AUTH_USERNAME)
    password_matches = _password_context.verify(password, _admin_password_hash)
    return username_matches and password_matches
