"""FastAPI application: the API endpoints and error handling."""

import logging
import os
import sqlite3
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import database
from options import STATUS_DISCHARGED
from schemas import Patient, PatientInput

logger = logging.getLogger("uvicorn.error")

# Frontend addresses that may call this API (comma separated).
DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
for vercel_env in ("VERCEL_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
    vercel_host = os.getenv(vercel_env)
    if vercel_host:
        DEFAULT_ORIGINS += f",https://{vercel_host}"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",")
    if origin.strip()
]

# Largest integer SQLite can store.
MAX_PATIENT_ID = 9223372036854775807
PatientId = Annotated[int, Path(ge=1, le=MAX_PATIENT_ID)]

app = FastAPI(title="Patient Admission Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)

database.init_db()


# ---------- Error handling ----------


def get_error_message(error, field):
    """Convert one Pydantic error into a simple message."""
    label = field.replace("_", " ").capitalize()
    if error["type"] == "json_invalid":
        return "Request body is not valid JSON."
    if error["type"] == "missing":
        return f"{label} is required."
    if error["type"] == "extra_forbidden":
        return f"{label} is not an allowed field."
    if error["type"] == "value_error":
        # These are the messages written in schemas.py.
        return str(error["ctx"]["error"])
    return f"{label}: {error['msg']}."


@app.exception_handler(RequestValidationError)
def handle_validation_error(request: Request, exc: RequestValidationError):
    """Return validation errors as {"detail": ..., "errors": {field: message}}."""
    errors = {}
    for error in exc.errors():
        location = error["loc"]  # for example ("body", "age")
        if error["type"] == "json_invalid" or len(location) < 2:
            field = "request_body"
        else:
            field = str(location[1])
        errors[field] = get_error_message(error, field)

    return JSONResponse(
        status_code=422,
        content={"detail": "Validation failed.", "errors": errors},
    )


@app.exception_handler(sqlite3.Error)
def handle_database_error(request: Request, exc: sqlite3.Error):
    """Log the real error on the server, but send only a general message."""
    logger.error("Database error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred. Please try again."},
    )


def get_patient_or_404(patient_id):
    patient = database.get_patient(patient_id)
    if patient is None:
        raise HTTPException(404, f"Patient with ID {patient_id} was not found.")
    return patient


# ---------- Endpoints ----------


@app.post("/patients", status_code=201, response_model=Patient)
def create_patient(patient: PatientInput):
    patient_id = database.create_patient(patient)
    return get_patient_or_404(patient_id)


@app.get("/patients", response_model=list[Patient])
def list_patients(
    search: str = "", ward: str = "", department: str = "", doctor: str = ""
):
    return database.get_patients(search.strip(), ward, department, doctor)


@app.get("/patients/{patient_id}", response_model=Patient)
def get_patient(patient_id: PatientId):
    return get_patient_or_404(patient_id)


@app.put("/patients/{patient_id}", response_model=Patient)
def update_patient(patient_id: PatientId, patient: PatientInput):
    if not database.update_patient(patient_id, patient):
        raise HTTPException(404, f"Patient with ID {patient_id} was not found.")
    return get_patient_or_404(patient_id)


@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: PatientId):
    if not database.delete_patient(patient_id):
        raise HTTPException(404, f"Patient with ID {patient_id} was not found.")
    return {"message": "Patient deleted successfully."}


@app.patch("/patients/{patient_id}/discharge", response_model=Patient)
def discharge_patient(patient_id: PatientId):
    patient = get_patient_or_404(patient_id)
    if patient["status"] == STATUS_DISCHARGED:
        raise HTTPException(409, "Patient is already discharged.")
    database.discharge_patient(patient_id)
    return get_patient_or_404(patient_id)
