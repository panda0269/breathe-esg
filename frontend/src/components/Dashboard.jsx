import { useState, useEffect } from "react"
import axios from "axios"

export default function Dashboard({ api, clientId }) {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    axios.get(`${api}/dashboard/?client_id=${clientId}`)
      .then(res => setStats(res.data))
  }, [clientId])

  if (!stats) return <p>Loading...</p>

  return (
    <div className="dashboard">
      <h2>Overview</h2>

      <div className="stat-cards">
        <div className="card total">
          <h3>Total Records</h3>
          <p>{stats.total}</p>
        </div>
        <div className="card pending">
          <h3>Pending Review</h3>
          <p>{stats.pending}</p>
        </div>
        <div className="card approved">
          <h3>Approved</h3>
          <p>{stats.approved}</p>
        </div>
        <div className="card flagged">
          <h3>Flagged</h3>
          <p>{stats.flagged}</p>
        </div>
        <div className="card rejected">
          <h3>Rejected</h3>
          <p>{stats.rejected}</p>
        </div>
      </div>

      <div className="breakdown">
        <div className="breakdown-section">
          <h3>By Source</h3>
          {Object.entries(stats.by_source).map(([key, val]) => (
            <div key={key} className="breakdown-row">
              <span>{key}</span>
              <span>{val}</span>
            </div>
          ))}
        </div>
        <div className="breakdown-section">
          <h3>By Scope</h3>
          {Object.entries(stats.by_scope).map(([key, val]) => (
            <div key={key} className="breakdown-row">
              <span>{key}</span>
              <span>{val}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}