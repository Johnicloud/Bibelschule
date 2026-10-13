"""Passwort-Hashing: PBKDF2-HMAC-SHA256 aus der Standardbibliothek, keine zusätzliche Abhängigkeit.
Reine Rechnung, kein Speicher, kein Zugriff auf eine Uhr (passt zur Domäne)."""
import hashlib
import hmac
import secrets

ITERATIONEN = 600_000


def hash_password(password: str, salt: str | None = None) -> str:
    """Liefert 'salz$hash' (beides hex). Ohne salt wird ein neues erzeugt (zum Anlegen eines Kontos)."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), ITERATIONEN)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, _ = password_hash.split("$", 1)
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, salt), password_hash)
