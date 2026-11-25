import { DEPARTMENTS, DOCTORS, WARDS } from '../options'

// Search box and the three filter dropdowns. The values are stored in App.jsx.
function Filters({ filters, onChange, onClear }) {
  function handleChange(event) {
    const { name, value } = event.target
    onChange({ ...filters, [name]: value })
  }

  function renderSelect(name, label, options) {
    return (
      <div className="field">
        <label htmlFor={`filter-${name}`}>{label}</label>
        <select id={`filter-${name}`} name={name} value={filters[name]} onChange={handleChange}>
          <option value="">All</option>
          {options.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      </div>
    )
  }

  return (
    <div className="filters">
      <div className="field">
        <label htmlFor="filter-search">Search by name</label>
        <input id="filter-search" name="search" type="text" placeholder="Enter patient name"
          value={filters.search} onChange={handleChange} />
      </div>
      {renderSelect('ward', 'Ward', WARDS)}
      {renderSelect('department', 'Department', DEPARTMENTS)}
      {renderSelect('doctor', 'Doctor', DOCTORS)}
      <button type="button" onClick={onClear}>Clear</button>
    </div>
  )
}

export default Filters
