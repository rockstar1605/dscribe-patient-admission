"""Database layer: uses PostgreSQL when DATABASE_URL is set, otherwise local SQLite.

Every query uses parameterized placeholders so user input is never joined into SQL.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from options import STATUS_ADMITTED, STATUS_DISCHARGED

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")

DEFAULT_DATABASE_PATH = (
    Path("/tmp/patients.db")
    if os.getenv("VERCEL")
    else Path(__file__).parent / "patients.db"
)
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DEFAULT_DATABASE_PATH))

DB_ERRORS = (sqlite3.Error, psycopg.Error)

CREATE_TABLE_SQLITE = """
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

CREATE_TABLE_POSTGRES = """
CREATE TABLE IF NOT EXISTS patients (
    id             SERIAL  PRIMARY KEY,
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
    if DATABASE_URL:
        connection = psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=10)
    else:
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def execute_query(connection, query, params=()):
    """Run a query using the active database's placeholder style."""
    if DATABASE_URL:
        query = query.replace("?", "%s")
    return connection.execute(query, params)


def init_db():
    with get_connection() as connection:
        sql = CREATE_TABLE_POSTGRES if DATABASE_URL else CREATE_TABLE_SQLITE
        connection.execute(sql)


def get_patients(search, ward, department, doctor):
    """Return patients matching all of the given conditions. Empty ones are skipped."""
    conditions = []
    values = []

    if search:
        # STRPOS (Postgres) / INSTR (SQLite) finds text anywhere in name, ignoring case.
        fn = "STRPOS" if DATABASE_URL else "INSTR"
        conditions.append(f"{fn}(LOWER(name), LOWER(?)) > 0")
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
        rows = execute_query(connection, query, values).fetchall()
    return [dict(row) for row in rows]


def get_patient(patient_id):
    """Return one patient as a dictionary, or None if the ID does not exist."""
    with get_connection() as connection:
        row = execute_query(
            connection, "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
    return dict(row) if row else None


def create_patient(patient):
    """Insert a new patient and return the generated ID."""
    params = (
        patient.name,
        patient.age,
        patient.gender,
        patient.ward,
        patient.department,
        patient.doctor,
        patient.admission_date.isoformat(),
        STATUS_ADMITTED,
    )
    query = """
        INSERT INTO patients
            (name, age, gender, ward, department, doctor, admission_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as connection:
        if DATABASE_URL:
            row = execute_query(
                connection, query + " RETURNING id", params
            ).fetchone()
            return row["id"]
        cursor = execute_query(connection, query, params)
        return cursor.lastrowid


def update_patient(patient_id, patient):
    """Update a patient. Return False if the ID does not exist."""
    with get_connection() as connection:
        cursor = execute_query(
            connection,
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
        cursor = execute_query(
            connection, "DELETE FROM patients WHERE id = ?", (patient_id,)
        )
    return cursor.rowcount > 0


def discharge_patient(patient_id):
    """Change only the status. The record stays in the table."""
    with get_connection() as connection:
        execute_query(
            connection,
            "UPDATE patients SET status = ? WHERE id = ?",
            (STATUS_DISCHARGED, patient_id),
        )
