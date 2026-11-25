import { useEffect, useState } from 'react'
import { deletePatient, dischargePatient, getPatients } from './api'
import Filters from './components/Filters'
import PatientForm from './components/PatientForm'
import PatientTable from './components/PatientTable'

const EMPTY_FILTERS = { search: '', ward: '', department: '', doctor: '' }

function App() {
  const [patients, setPatients] = useState([])
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingPatient, setEditingPatient] = useState(null) // null means "add"
  const [refreshCount, setRefreshCount] = useState(0) // increase it to reload the list

  // Load patients on the first render, when a filter changes, and after every change.
  useEffect(() => {
    // If the user types quickly, an older request may finish after a newer one.
    // The cleanup function below marks older requests so their results are ignored.
    let ignore = false

    async function loadPatients() {
      setLoading(true)
      try {
        const data = await getPatients(filters)
        if (ignore) return
        setPatients(data)
        setLoadError('')
      } catch (error) {
        if (ignore) return
        setLoadError(error.message)
      }
      setLoading(false)
    }

    loadPatients()
    return () => {
      ignore = true
    }
  }, [filters, refreshCount])

  function clearMessages() {
    setSuccessMessage('')
    setErrorMessage('')
  }

  function refreshPatients() {
    setRefreshCount((count) => count + 1)
  }

  function openForm(patient) {
    clearMessages()
    setEditingPatient(patient)
    setShowForm(true)
  }

  function handleSaved(message) {
    setShowForm(false)
    setSuccessMessage(message)
    refreshPatients()
  }

  // Shared by delete and discharge: confirm, call the API, show the result, refresh.
  async function runAction(question, apiCall, message) {
    if (!window.confirm(question)) return
    clearMessages()
    try {
      await apiCall()
      setSuccessMessage(message)
    } catch (error) {
      setErrorMessage(error.message)
    }
    // Also refresh after a failure, because the list on screen may be out of date.
    refreshPatients()
  }

  function handleDelete(patient) {
    runAction(
      `Delete patient "${patient.name}" (ID ${patient.id})? This cannot be undone.`,
      () => deletePatient(patient.id),
      'Patient deleted successfully.',
    )
  }

  function handleDischarge(patient) {
    runAction(
      `Mark patient "${patient.name}" (ID ${patient.id}) as discharged?`,
      () => dischargePatient(patient.id),
      'Patient discharged successfully.',
    )
  }

  if (showForm) {
    return (
      <main className="container">
        <h1>Patient Admission Management</h1>
        <PatientForm
          patient={editingPatient}
          onSaved={handleSaved}
          onCancel={() => setShowForm(false)}
        />
      </main>
    )
  }

  return (
    <main className="container">
      <div className="page-header">
        <h1>Patient Admission Management</h1>
        <button className="primary" onClick={() => openForm(null)}>Add Patient</button>
      </div>

      {successMessage && <p className="message success" role="status">{successMessage}</p>}
      {errorMessage && <p className="message error" role="alert">{errorMessage}</p>}

      <Filters filters={filters} onChange={setFilters} onClear={() => setFilters(EMPTY_FILTERS)} />

      <p className="list-info">
        {loading && 'Loading patients...'}
        {!loading && !loadError && `Patients: ${patients.length}`}
      </p>

      {loadError && (
        <p className="message error" role="alert">
          {loadError} <button onClick={refreshPatients}>Try again</button>
        </p>
      )}

      {/* While loading for the first time there is nothing to show yet. */}
      {!loadError && !(loading && patients.length === 0) && (
        <PatientTable
          patients={patients}
          onEdit={openForm}
          onDischarge={handleDischarge}
          onDelete={handleDelete}
        />
      )}
    </main>
  )
}

export default App
