"""Request and response models. All backend validation rules live here."""

import re
from datetime import date, datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, field_validator

from options import DEPARTMENTS, DOCTORS, GENDERS, WARDS

MIN_AGE = 0
MAX_AGE = 120

# Letters, with spaces allowed between words.
NAME_PATTERN = re.compile(r"[A-Za-z ]+")

DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

# "Today" is always the date in India, even if the server runs in another timezone.
INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def get_today():
    return datetime.now(INDIA_TIMEZONE).date()


def check_choice(value, allowed_values, label):
    """Check that a dropdown value was given and is one of the allowed values."""
    if value is None or value == "":
        raise ValueError(f"{label} is required.")
    if value not in allowed_values:
        raise ValueError(f"{label} must be one of: {', '.join(allowed_values)}.")
    return value


def parse_date(value):
    """Convert a YYYY-MM-DD string to a date, or raise a ValueError."""
    message = "Admission date must be a valid date (YYYY-MM-DD)."
    if not isinstance(value, str) or not DATE_PATTERN.fullmatch(value):
        raise ValueError(message)
    try:
        return date.fromisoformat(value)
    except ValueError:
        # Correct format but not a real date, for example 2026-02-30.
        raise ValueError(message)


class PatientInput(BaseModel):
    """Data sent by the client when creating or updating a patient.

    Status is not included: a new patient is always Admitted, and the status
    is changed only by the discharge endpoint.
    """

    # Reject unknown fields instead of silently ignoring them.
    model_config = ConfigDict(extra="forbid")

    name: str
    age: int
    gender: str
    ward: str
    department: str
    doctor: str
    admission_date: date

    # mode="before" runs our check on the raw value, before Pydantic converts it.
    # This lets us return our own clear error messages.

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value):
        if value is None:
            raise ValueError("Name is required.")
        if not isinstance(value, str):
            raise ValueError("Name must be text.")
        name = value.strip()
        if name == "":
            raise ValueError("Name is required.")
        if not NAME_PATTERN.fullmatch(name):
            raise ValueError("Name must contain letters only.")
        return name

    @field_validator("age", mode="before")
    @classmethod
    def validate_age(cls, value):
        if value is None or value == "":
            raise ValueError("Age is required.")
        # In Python True and False are also ints, so they are rejected separately.
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("Age must be a whole number.")
        if value < MIN_AGE or value > MAX_AGE:
            raise ValueError(f"Age must be between {MIN_AGE} and {MAX_AGE}.")
        return value

    @field_validator("gender", mode="before")
    @classmethod
    def validate_gender(cls, value):
        return check_choice(value, GENDERS, "Gender")

    @field_validator("ward", mode="before")
    @classmethod
    def validate_ward(cls, value):
        return check_choice(value, WARDS, "Ward")

    @field_validator("department", mode="before")
    @classmethod
    def validate_department(cls, value):
        return check_choice(value, DEPARTMENTS, "Department")

    @field_validator("doctor", mode="before")
    @classmethod
    def validate_doctor(cls, value):
        return check_choice(value, DOCTORS, "Doctor")

    @field_validator("admission_date", mode="before")
    @classmethod
    def validate_admission_date(cls, value):
        if value is None or value == "":
            raise ValueError("Admission date is required.")
        admission_date = parse_date(value)
        if admission_date > get_today():
            raise ValueError("Admission date cannot be in the future.")
        return admission_date


class Patient(BaseModel):
    """A patient record returned to the client."""

    id: int
    name: str
    age: int
    gender: str
    ward: str
    department: str
    doctor: str
    admission_date: date
    status: str
