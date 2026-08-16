"""
HealthSync AI - Security Utilities

Responsibilities:
    - Password hashing
    - Password verification
    - Secure session-token generation

IMPORTANT:
    - Plaintext passwords are never stored.
    - Password hashes are one-way.
    - Session tokens are generated using Python's
      cryptographically secure random generator.
    - No credentials or secret keys are hardcoded here.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


# ============================================================
# PASSWORD CONFIGURATION
# ============================================================

PASSWORD_ALGORITHM = "pbkdf2_sha256"

PASSWORD_ITERATIONS = 600_000

SALT_BYTES = 32

HASH_BYTES = 32


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    """
    Create a secure password hash.

    Format:

        pbkdf2_sha256$iterations$salt$hash

    The returned value is safe to store in the users table.

    The original password is never stored.
    """

    if not isinstance(password, str):
        raise TypeError("Password must be a string.")

    if not password:
        raise ValueError("Password cannot be empty.")

    salt = secrets.token_bytes(SALT_BYTES)

    password_bytes = password.encode("utf-8")

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        PASSWORD_ITERATIONS,
        dklen=HASH_BYTES,
    )

    salt_encoded = base64.urlsafe_b64encode(
        salt
    ).decode("ascii")

    hash_encoded = base64.urlsafe_b64encode(
        derived_key
    ).decode("ascii")

    return (
        f"{PASSWORD_ALGORITHM}$"
        f"{PASSWORD_ITERATIONS}$"
        f"{salt_encoded}$"
        f"{hash_encoded}"
    )


# ============================================================
# PASSWORD VERIFICATION
# ============================================================

def verify_password(
    password: str,
    stored_hash: str,
) -> bool:
    """
    Verify a password against a previously generated hash.

    Returns:
        True  -> password is correct
        False -> password is incorrect
    """

    if not isinstance(password, str):
        return False

    if not isinstance(stored_hash, str):
        return False

    try:
        algorithm, iterations_text, salt_encoded, hash_encoded = (
            stored_hash.split("$", 3)
        )

        if algorithm != PASSWORD_ALGORITHM:
            return False

        iterations = int(iterations_text)

        salt = base64.urlsafe_b64decode(
            salt_encoded.encode("ascii")
        )

        expected_hash = base64.urlsafe_b64decode(
            hash_encoded.encode("ascii")
        )

    except (
        ValueError,
        TypeError,
        UnicodeError,
    ):
        return False

    calculated_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=len(expected_hash),
    )

    return hmac.compare_digest(
        calculated_hash,
        expected_hash,
    )


# ============================================================
# SESSION TOKEN
# ============================================================

def generate_session_token() -> str:
    """
    Generate a cryptographically secure session token.

    This token will be stored in the local sessions table
    for persistent login.

    It does not contain the user's password.
    """

    return secrets.token_urlsafe(48)


# ============================================================
# TOKEN COMPARISON
# ============================================================

def compare_tokens(
    token_a: str,
    token_b: str,
) -> bool:
    """
    Safely compare two session tokens.
    """

    if not isinstance(token_a, str):
        return False

    if not isinstance(token_b, str):
        return False

    return hmac.compare_digest(
        token_a,
        token_b,
    )


# ============================================================
# PASSWORD VALIDATION
# ============================================================

def validate_password(password: str) -> tuple[bool, str]:
    """
    Perform basic password validation before hashing.

    Returns:

        (True, "")
            Password is acceptable.

        (False, "reason")
            Password is not acceptable.

    This function does not store or hash the password.
    """

    if not isinstance(password, str):
        return False, "Password must be text."

    if not password:
        return False, "Password cannot be empty."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    if len(password) > 128:
        return False, "Password must not exceed 128 characters."

    return True, ""


# ============================================================
# MODULE EXPORTS
# ============================================================

__all__ = [
    "hash_password",
    "verify_password",
    "generate_session_token",
    "compare_tokens",
    "validate_password",
]