"""
HealthSync AI - Validation Utilities

Reusable validation helpers for:
    - Name
    - Email
    - Phone
    - User input
    - Health profile values

This module does NOT:
    - Access the database
    - Access BLE
    - Generate sensor values
    - Perform authentication
"""

from __future__ import annotations

import re


# ============================================================
# NAME
# ============================================================

def validate_name(name: str) -> tuple[bool, str]:
    """Validate a user's name."""

    if not isinstance(name, str):
        return False, "Name must be text."

    name = name.strip()

    if not name:
        return False, "Name cannot be empty."

    if len(name) > 100:
        return False, "Name is too long."

    if not re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", name):
        return False, "Name contains invalid characters."

    return True, ""


# ============================================================
# EMAIL
# ============================================================

def validate_email(email: str) -> tuple[bool, str]:
    """Validate an email address."""

    if not isinstance(email, str):
        return False, "Email must be text."

    email = email.strip()

    if not email:
        return False, "Email cannot be empty."

    if len(email) > 254:
        return False, "Email is too long."

    pattern = (
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[A-Za-z0-9-]+"
        r"(?:\.[A-Za-z0-9-]+)+$"
    )

    if not re.fullmatch(pattern, email):
        return False, "Enter a valid email address."

    return True, ""


# ============================================================
# PHONE
# ============================================================

def validate_phone(phone: str) -> tuple[bool, str]:
    """Validate a phone number."""

    if not isinstance(phone, str):
        return False, "Phone number must be text."

    phone = phone.strip()

    if not phone:
        return False, "Phone number cannot be empty."

    digits = re.sub(r"\D", "", phone)

    if not 7 <= len(digits) <= 15:
        return False, "Enter a valid phone number."

    return True, ""


# ============================================================
# BLOOD GROUP
# ============================================================

def validate_blood_group(
    blood_group: str,
) -> tuple[bool, str]:
    """Validate a blood group."""

    if not isinstance(blood_group, str):
        return False, "Blood group must be text."

    value = blood_group.strip().upper()

    valid_groups = {
        "A+",
        "A-",
        "B+",
        "B-",
        "AB+",
        "AB-",
        "O+",
        "O-",
    }

    if value not in valid_groups:
        return False, "Invalid blood group."

    return True, ""


# ============================================================
# POSITIVE NUMBER
# ============================================================

def validate_positive_number(
    value: float | int | str,
    field_name: str = "Value",
) -> tuple[bool, str]:
    """Validate a positive numeric value."""

    try:
        number = float(value)
    except (TypeError, ValueError):
        return False, f"{field_name} must be a number."

    if number <= 0:
        return False, f"{field_name} must be greater than zero."

    return True, ""


# ============================================================
# OPTIONAL NUMBER
# ============================================================

def validate_optional_number(
    value: float | int | str | None,
    field_name: str = "Value",
) -> tuple[bool, str]:
    """Validate a numeric value that may be empty."""

    if value is None or value == "":
        return True, ""

    try:
        float(value)
    except (TypeError, ValueError):
        return False, f"{field_name} must be a number."

    return True, ""


# ============================================================
# RANGE
# ============================================================

def validate_range(
    value: float | int | str,
    minimum: float,
    maximum: float,
    field_name: str = "Value",
) -> tuple[bool, str]:
    """Validate that a number falls within a specified range."""

    try:
        number = float(value)
    except (TypeError, ValueError):
        return False, f"{field_name} must be a number."

    if number < minimum or number > maximum:
        return (
            False,
            f"{field_name} must be between "
            f"{minimum} and {maximum}.",
        )

    return True, ""


# ============================================================
# USER REGISTRATION
# ============================================================

def validate_registration(
    name: str,
    email: str,
    password: str,
) -> tuple[bool, str]:
    """
    Validate the basic registration fields.

    Password strength rules are handled by security.py.
    """

    valid, message = validate_name(name)

    if not valid:
        return False, message

    valid, message = validate_email(email)

    if not valid:
        return False, message

    if not isinstance(password, str) or not password:
        return False, "Password cannot be empty."

    return True, ""


# ============================================================
# MODULE EXPORTS
# ============================================================

__all__ = [
    "validate_name",
    "validate_email",
    "validate_phone",
    "validate_blood_group",
    "validate_positive_number",
    "validate_optional_number",
    "validate_range",
    "validate_registration",
]