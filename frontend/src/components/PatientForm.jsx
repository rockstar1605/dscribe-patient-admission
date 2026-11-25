import { useState } from 'react'
import { createPatient, updatePatient } from '../api'
import { DEPARTMENTS, DOCTORS, GENDERS, WARDS } from '../options'
import { getToday, validatePatient } from '../validation'

const EMPTY_VALUES = {
  name: '',
  age: '',
  gender: '',
  ward: '',
  department: '',
  doctor: '',
  admission_date: '',
}

// Copies only the editable fields. Inputs work with text, so age becomes a string.
function getInitialValues(patient) {
  if (!patient) return EMPTY_VALUES
  return {
    name: patient.name,
    age: String(patient.age),
    gender: patient.gender,
    ward: patient.ward,
    department: patient.department,
    doctor: patient.doctor,
    admission_date: patient.admission_date,
  }
}

// One labelled form field with its error message below it.
function Field({ id, label, error, children }) {
  return (
    <div className="field">
      <label htmlFor={id}>{label} *</label>
      {children}
      {error && <span className="field-error">{error}</span>}
    </div>
  )
}

// Used for both adding (patient is null) and editing (patient is an existing record).
function PatientForm({ patient, onSaved, onCancel }) {
  const [values, setValues] = useState(getInitialValues(patient))
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  function handleChange(event) {
    const { name, value } = event.target
    setValues({ ...values, [name]: value })
    setErrors({ ...errors, [name]: '' })
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError('')

    const validationErrors = validatePatient(values)
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    const data = { ...values, name: values.name.trim(), age: Number(values.age) }

    setSaving(true)
    try {
      if (patient) {
        await updatePatient(patient.id, data)
        onSaved('Patient updated successfully.')
      } else {
        await createPatient(data)
        onSaved('Patient added successfully.')
      }
    } catch (error) {
      setFormError(error.message)
      setErrors(error.fieldErrors || {})
      setSaving(false)
    }
  }

  function renderSelect(name, label, options) {
    return (
      <Field id={name} label={label} error={errors[name]}>
        <select id={name} name={name} value={values[name]} onChange={handleChange}>
          <option value="">Select {label.toLowerCase()}</option>
          {options.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      </Field>
    )
  }

  // noValidate turns off the browser's own popups so our messages are shown instead.
  return (
    <form className="patient-form" onSubmit={handleSubmit} noValidate>
      <h2>{patient ? `Edit Patient (ID ${patient.id})` : 'Add Patient'}</h2>
      {formError && <p className="message error" role="alert">{formError}</p>}

      <div className="form-grid">
        <Field id="name" label="Name" error={errors.name}>
          <input id="name" name="name" type="text" value={values.name} onChange={handleChange} />
        </Field>

        <Field id="age" label="Age" error={errors.age}>
          <input id="age" name="age" type="number" min="0" max="120"
            value={values.age} onChange={handleChange} />
        </Field>

        {renderSelect('gender', 'Gender', GENDERS)}
        {renderSelect('ward', 'Ward', WARDS)}
        {renderSelect('department', 'Department', DEPARTMENTS)}
        {renderSelect('doctor', 'Doctor', DOCTORS)}

        <Field id="admission_date" label="Admission Date" error={errors.admission_date}>
          <input id="admission_date" name="admission_date" type="date" max={getToday()}
            value={values.admission_date} onChange={handleChange} />
        </Field>
      </div>

      <div className="form-buttons">
        <button type="submit" className="primary" disabled={saving}>
          {saving ? 'Saving...' : 'Save'}
        </button>
        <button type="button" onClick={onCancel} disabled={saving}>Cancel</button>
      </div>
    </form>
  )
}

export default PatientForm
