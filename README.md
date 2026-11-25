# Patient Admission Management App

A web app where hospital staff can manage admitted patients: add, view, search, filter, edit, discharge and delete patient records.

Built for the DScribe Software Engineer Intern Round 1 task.

**Live link:** https://dscribe-patient-admission.vercel.app

## Tech stack

| Part | Technology |
|---|---|
| Frontend | React.js 19 (JavaScript, HTML, plain CSS), with Vite as the development/build tool |
| Backend | Python, FastAPI, Pydantic (validation), Uvicorn (server) |
| Database | SQLite, using Python's built-in `sqlite3` module |
| Communication | REST API with JSON |

Node.js is only used to run the Vite tool. There is no Node.js backend.

## Folder structure

```
dscribe-patient-admission/
├── backend/
│   ├── main.py            API endpoints, CORS and error handling
│   ├── vercel_app.py      Vercel entrypoint mounting the API at /api
│   ├── schemas.py         Request/response models and all backend validation
│   ├── database.py        All SQLite queries
│   ├── options.py         Allowed dropdown values
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx       Starts React
│       ├── App.jsx        Main state, loads the list, delete and discharge
│       ├── api.js         All calls to the backend (and the backend URL)
│       ├── validation.js  All frontend validation
│       ├── options.js     Allowed dropdown values
│       ├── styles.css
│       └── components/
│           ├── Filters.jsx       Search box and filter dropdowns
│           ├── PatientForm.jsx   Form used for both add and edit
│           └── PatientTable.jsx  Patient list and row actions
├── vercel.json
└── README.md
```

## Implemented features

1. Add a patient (status is set to Admitted)
2. View the list of all patients
3. Filter by Ward, Department and Doctor (can be combined)
4. Search patients by name (partial match, ignores letter case, works with the filters)
5. Edit a patient
6. Delete a patient (with confirmation)
7. Mark a patient as Discharged (with confirmation; the record is kept)
8. Responsive layout for mobile, tablet and desktop

## API endpoints

| Method | URL | Purpose | Success | Errors |
|---|---|---|---|---|
| POST | `/patients` | Add a patient | 201 | 422 |
| GET | `/patients` | List patients. Optional query parameters: `search`, `ward`, `department`, `doctor` | 200 | |
| GET | `/patients/{patient_id}` | Get one patient | 200 | 404, 422 |
| PUT | `/patients/{patient_id}` | Update a patient | 200 | 404, 422 |
| DELETE | `/patients/{patient_id}` | Delete a patient | 200 | 404, 422 |
| PATCH | `/patients/{patient_id}/discharge` | Change status to Discharged | 200 | 404, 409 (already discharged), 422 |

Example body for POST and PUT:

```json
{
  "name": "Rahul Sharma",
  "age": 45,
  "gender": "Male",
  "ward": "ICU",
  "department": "Cardiology",
  "doctor": "Dr. Sharma",
  "admission_date": "2026-11-20"
}
```

Example validation error (status 422):

```json
{
  "detail": "Validation failed.",
  "errors": {
    "name": "Name must contain letters only.",
    "age": "Age must be between 0 and 120."
  }
}
```

A database failure returns status 500 with a general message. The details are only logged on the server.

## Validation rules

The same rules are checked in the frontend (`validation.js`) and again in the backend (`schemas.py`).

| Field | Rule |
|---|---|
| Name | Required, letters only (A-Z, spaces allowed between words). Outer spaces are removed. |
| Age | Required, whole number from 0 to 120 |
| Gender | Required: Male, Female, Other |
| Ward | Required: General Ward, ICU, Emergency, Private Ward |
| Department | Required: Cardiology, Neurology, Orthopedics, General Medicine, Pediatrics |
| Doctor | Required: Dr. Sharma, Dr. Verma, Dr. Mehta, Dr. Gupta |
| Admission Date | Required, valid date, cannot be in the future. "Today" is the current date in India (IST) on both sides. |

Status is not typed in by the user. It starts as Admitted and is changed only by the Discharge action. The backend rejects unknown fields.

## Database

Locally, SQLite stores everything in one file, `backend/patients.db`. The file and its single `patients` table are created automatically when the backend starts. Because it is a file on disk, data stays saved after a server restart. The file is not committed to Git.

| Column | Type | Constraint |
|---|---|---|
| id | INTEGER | Primary key, generated automatically |
| name | TEXT | NOT NULL |
| age | INTEGER | NOT NULL, between 0 and 120 |
| gender | TEXT | NOT NULL |
| ward | TEXT | NOT NULL |
| department | TEXT | NOT NULL |
| doctor | TEXT | NOT NULL |
| admission_date | TEXT | NOT NULL, stored as YYYY-MM-DD |
| status | TEXT | NOT NULL, Admitted or Discharged |

All queries use `?` placeholders to prevent SQL injection.

## How the parts communicate

```
React (browser)  -- HTTP + JSON -->  FastAPI  -- SQL -->  SQLite file
```

Example, adding a patient:

1. `PatientForm.jsx` runs the frontend validation.
2. `api.js` sends `POST /patients` with the data as JSON.
3. FastAPI converts the JSON to a `PatientInput` object, which runs the backend validation. If something is wrong it returns 422 and the form shows the messages next to the fields.
4. `database.py` inserts the row into SQLite.
5. FastAPI returns the new record as JSON with status 201.
6. React shows a success message and loads the list again with `GET /patients`.
