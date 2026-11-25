import { STATUS_ADMITTED } from '../options'

// "2026-11-05" -> "05-11-2026"
function formatDate(isoDate) {
  return isoDate.split('-').reverse().join('-')
}

function PatientTable({ patients, onEdit, onDischarge, onDelete }) {
  if (patients.length === 0) {
    return <p className="empty">No patients found.</p>
  }

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Patient ID</th>
            <th>Name</th>
            <th>Age</th>
            <th>Gender</th>
            <th>Ward</th>
            <th>Department</th>
            <th>Doctor</th>
            <th>Admission Date</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {patients.map((patient) => (
            <tr key={patient.id}>
              <td>{patient.id}</td>
              <td className="name">{patient.name}</td>
              <td>{patient.age}</td>
              <td>{patient.gender}</td>
              <td>{patient.ward}</td>
              <td>{patient.department}</td>
              <td>{patient.doctor}</td>
              <td>{formatDate(patient.admission_date)}</td>
              <td>
                <span className={`status ${patient.status.toLowerCase()}`}>{patient.status}</span>
              </td>
              <td className="actions">
                <button onClick={() => onEdit(patient)}>Edit</button>
                <button className="danger" onClick={() => onDelete(patient)}>Delete</button>
                {patient.status === STATUS_ADMITTED && (
                  <button onClick={() => onDischarge(patient)}>Discharge</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default PatientTable
