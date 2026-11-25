"""All SQLite code: creating the table and reading/writing patient records.

Every query uses "?" placeholders, so user input is never joined into the SQL.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from options import STATUS_ADMITTED, STATUS_DISCHARGED

# The database is a normal file on disk locally; on Vercel only /tmp is writable.
DEFAULT_DATABASE_PATH = (
    Path("/tmp/patients.db")
    if os.getenv("VERCEL")
    else Path(__file__).parent / "patients.db"
)
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DEFAULT_DATABASE_PATH))

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS patients (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    age            INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    gender         TEXT    NOT NULL,
    ward           TEXT    NOT NULL,
    department     TEXT    NOT NULL,
    doctor         TEXT    NOT NULL,
    admission_date TEXT    NOT NULL,
    status         TEXT    NOT NULL DEFAULT 'Admitted'
                   CHECK (status IN ('Admitted', 'Discharged'))
)
"""


@contextmanager
def get_connection():
    """Open a connection, commit if everything worked, and always close it."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row  # allows reading columns by name
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db():
    with get_connection() as connection:
        connection.execute(CREATE_TABLE_SQL)


def get_patients(search, ward, department, doctor):
    """Return patients matching all of the given conditions. Empty ones are skipped."""
    conditions = []
    values = []

    if search:
        # INSTR finds the text anywhere in the name; LOWER ignores letter case.
        conditions.append("INSTR(LOWER(name), LOWER(?)) > 0")
        values.append(search)
    if ward:
        conditions.append("ward = ?")
        values.append(ward)
    if department:
        conditions.append("department = ?")
        values.append(department)
    if doctor:
        conditions.append("doctor = ?")
        values.append(doctor)

    query = "SELECT * FROM patients"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"

    with get_connection() as connection:
        rows = connection.execute(query, values).fetchall()
    return [dict(row) for row in rows]


def get_patient(patient_id):
    """Return one patient as a dictionary, or None if the ID does not exist."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
    return dict(row) if row else None


def create_patient(patient):
    """Insert a new patient and return the generated ID."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO patients
                (name, age, gender, ward, department, doctor, admission_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient.name,
                patient.age,
                patient.gender,
                patient.ward,
                patient.department,
                patient.doctor,
                patient.admission_date.isoformat(),
                STATUS_ADMITTED,
            ),
        )
    return cursor.lastrowid


def update_patient(patient_id, patient):
    """Update a patient. Return False if the ID does not exist."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE patients
            SET name = ?, age = ?, gender = ?, ward = ?,
                department = ?, doctor = ?, admission_date = ?
            WHERE id = ?
            """,
            (
                patient.name,
                patient.age,
                patient.gender,
                patient.ward,
                patient.department,
                patient.doctor,
                patient.admission_date.isoformat(),
                patient_id,
            ),
        )
    return cursor.rowcount > 0


def delete_patient(patient_id):
    """Delete a patient. Return False if the ID does not exist."""
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    return cursor.rowcount > 0


def discharge_patient(patient_id):
    """Change only the status. The record stays in the table."""
    with get_connection() as connection:
        connection.execute(
            "UPDATE patients SET status = ? WHERE id = ?",
            (STATUS_DISCHARGED, patient_id),
        )
