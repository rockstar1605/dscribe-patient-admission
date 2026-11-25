// Frontend validation. The same rules are checked again in backend/schemas.py.

import { DEPARTMENTS, DOCTORS, GENDERS, WARDS } from './options'

const MIN_AGE = 0
const MAX_AGE = 120

// Letters, with spaces allowed between words.
const NAME_PATTERN = /^[A-Za-z ]+$/

// Today's date in India as YYYY-MM-DD (the en-CA locale uses this format).
export function getToday() {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' })
}

function validateName(value) {
  const name = value.trim()
  if (name === '') return 'Name is required.'
  if (!NAME_PATTERN.test(name)) return 'Name must contain letters only.'
  return ''
}

function validateAge(value) {
  if (value === '') return 'Age is required.'
  const age = Number(value)
  if (!Number.isInteger(age)) return 'Age must be a whole number.'
  if (age < MIN_AGE || age > MAX_AGE) {
    return `Age must be between ${MIN_AGE} and ${MAX_AGE}.`
  }
  return ''
}

function validateChoice(value, allowedValues, label) {
  if (value === '') return `${label} is required.`
  if (!allowedValues.includes(value)) return `Please select a valid ${label.toLowerCase()}.`
  return ''
}

function validateAdmissionDate(value) {
  if (value === '') return 'Admission date is required.'
  // YYYY-MM-DD has a fixed length, so comparing text is the same as comparing dates.
  // Browsers allow years with more than 4 digits, so the length is checked too.
  if (value.length > 10 || value > getToday()) {
    return 'Admission date cannot be in the future.'
  }
  return ''
}

// Returns an object containing only the fields that have an error.
export function validatePatient(values) {
  const results = {
    name: validateName(values.name),
    age: validateAge(values.age),
    gender: validateChoice(values.gender, GENDERS, 'Gender'),
    ward: validateChoice(values.ward, WARDS, 'Ward'),
    department: validateChoice(values.department, DEPARTMENTS, 'Department'),
    doctor: validateChoice(values.doctor, DOCTORS, 'Doctor'),
    admission_date: validateAdmissionDate(values.admission_date),
  }

  const errors = {}
  for (const field in results) {
    if (results[field] !== '') errors[field] = results[field]
  }
  return errors
}
