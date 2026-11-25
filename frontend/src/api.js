// All communication with the FastAPI backend happens in this file.

const DEFAULT_API_URL = import.meta.env.DEV ? 'http://127.0.0.1:8000' : '/api'
const API_URL = (import.meta.env.VITE_API_URL || DEFAULT_API_URL).replace(/\/$/, '')

// Sends a request and returns the JSON response.
// On failure it throws an Error with:
//   error.message     - text to show the user
//   error.fieldErrors - validation errors from the backend, e.g. { age: '...' }
async function sendRequest(path, options = {}) {
  let response
  try {
    response = await fetch(API_URL + path, options)
  } catch {
    throw new Error('Cannot connect to the server. Please check that the backend is running.')
  }

  // data stays null if the response is not JSON.
  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const error = new Error(data?.detail || `Request failed (status ${response.status}).`)
    error.fieldErrors = data?.errors || {}
    throw error
  }
  return data
}

function sendJson(method, path, body) {
  return sendRequest(path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function getPatients(filters) {
  // URLSearchParams also encodes spaces and special characters.
  const query = new URLSearchParams(filters)
  return sendRequest(`/patients?${query}`)
}

export function createPatient(patient) {
  return sendJson('POST', '/patients', patient)
}

export function updatePatient(id, patient) {
  return sendJson('PUT', `/patients/${id}`, patient)
}

export function deletePatient(id) {
  return sendRequest(`/patients/${id}`, { method: 'DELETE' })
}

export function dischargePatient(id) {
  return sendRequest(`/patients/${id}/discharge`, { method: 'PATCH' })
}
