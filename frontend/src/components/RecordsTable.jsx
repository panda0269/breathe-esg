import { useState, useEffect } from "react"
import axios from "axios"

const STATUS_COLORS = {
  PENDING: "#f59e0b",
  APPROVED: "#10b981",
  REJECTED: "#ef4444",
  FLAGGED: "#f97316",
}

export default function RecordsTable({ api, clientId }) {
  const [records, setRecords] = useState([])
  const [filterStatus, setFilterStatus] = useState("")
  const [filterSource, setFilterSource] = useState("")
  const [notes, setNotes] = useState({})
  const [loading, setLoading] = useState(false)

  const fetchRecords = () => {
    let url = `${api}/records/?client_id=${clientId}`
    if (filterStatus) url += `&status=${filterStatus}`
    if (filterSource) url += `&source_type=${filterSource}`
    axios.get(url).then(res => setRecords(res.data))
  }

  useEffect(() => { fetchRecords() }, [clientId, filterStatus, filterSource])

  const review = (id, status) => {
    setLoading(true)
    axios.patch(`${api}/records/${id}/review/`, {
      status,
      notes: notes[id] || ""
    }).then(() => {
      fetchRecords()
      setLoading(false)
    })
  }

  return (
    <div className="records">
      <h2>Review Records</h2>

      <div className="filters">
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="PENDING">Pending</option>
          <option value="FLAGGED">Flagged</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
        </select>

        <select value={filterSource} onChange={e => setFilterSource(e.target.value)}>
          <option value="">All Sources</option>
          <option value="SAP">SAP</option>
          <option value="UTILITY">Utility</option>
          <option value="TRAVEL">Travel</option>
        </select>
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Source</th>
            <th>Scope</th>
            <th>Category</th>
            <th>Date</th>
            <th>Quantity</th>
            <th>Unit</th>
            <th>Location</th>
            <th>Vendor</th>
            <th>Status</th>
            <th>Notes</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {records.map(r => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.source_type}</td>
              <td>Scope {r.scope}</td>
              <td>{r.category}</td>
              <td>{r.activity_date}</td>
              <td>{r.quantity}</td>
              <td>{r.unit}</td>
              <td>{r.location || "—"}</td>
              <td>{r.vendor || "—"}</td>
              <td>
                <span className="badge" style={{ background: STATUS_COLORS[r.status] }}>
                  {r.status}
                </span>
              </td>
              <td>
                {!r.is_locked && (
                  <input
                    type="text"
                    placeholder="Add note..."
                    value={notes[r.id] || ""}
                    onChange={e => setNotes({ ...notes, [r.id]: e.target.value })}
                  />
                )}
                {r.is_locked && <span className="locked">🔒 Locked</span>}
              </td>
              <td>
                {!r.is_locked && (
                  <div className="action-buttons">
                    <button className="btn-approve" onClick={() => review(r.id, "APPROVED")} disabled={loading}>✓</button>
                    <button className="btn-reject" onClick={() => review(r.id, "REJECTED")} disabled={loading}>✗</button>
                    <button className="btn-flag" onClick={() => review(r.id, "FLAGGED")} disabled={loading}>⚑</button>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}