"""Vercel FastAPI entrypoint mounting the API routes under /api."""

from fastapi import FastAPI

from main import app as backend_app

app = FastAPI(title="Patient Admission Management API")
app.mount("/api", backend_app)
