import { useState, useEffect } from "react"
import axios from "axios"
import Dashboard from "./components/Dashboard"
import RecordsTable from "./components/RecordsTable"
import UploadForm from "./components/UploadForm"
import "./App.css"

const API = "http://127.0.0.1:8000/api"

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard")
  const [clients, setClients] = useState([])
  const [selectedClient, setSelectedClient] = useState(1)

  useEffect(() => {
    axios.get(`${API}/clients/`).then(res => setClients(res.data))
  }, [])

  return (
    <div className="app">
      <header className="header">
        <h1>Breathe ESG — Emissions Data Review</h1>
        <div className="client-select">
          <label>Client: </label>
          <select value={selectedClient} onChange={e => setSelectedClient(e.target.value)}>
            {clients.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
      </header>

      <nav className="tabs">
        <button className={activeTab === "dashboard" ? "active" : ""} onClick={() => setActiveTab("dashboard")}>Dashboard</button>
        <button className={activeTab === "records" ? "active" : ""} onClick={() => setActiveTab("records")}>Review Records</button>
        <button className={activeTab === "upload" ? "active" : ""} onClick={() => setActiveTab("upload")}>Upload Data</button>
      </nav>

      <main className="main">
        {activeTab === "dashboard" && <Dashboard api={API} clientId={selectedClient} />}
        {activeTab === "records" && <RecordsTable api={API} clientId={selectedClient} />}
        {activeTab === "upload" && <UploadForm api={API} clientId={selectedClient} onUploadSuccess={() => setActiveTab("dashboard")} />}``
      </main>
    </div>
  )
}