import { useState } from "react"
import axios from "axios"

export default function UploadForm({ api, clientId, onUploadSuccess }) {
  const [sourceType, setSourceType] = useState("SAP")
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const upload = () => {
    if (!file) return setError("Please select a file")
    setLoading(true)
    setResult(null)
    setError(null)

    const formData = new FormData()
    formData.append("client_id", clientId)
    formData.append("source_type", sourceType)
    formData.append("file", file)

     axios.post(`${api}/upload/`, formData)
      .then(res => {
        setResult(res.data)
        setLoading(false)
        if (onUploadSuccess) onUploadSuccess()
      })
     .catch(err => {
        const backendError = err.response?.data?.error || "Upload failed. Check file format.";
        setError(backendError);
        setLoading(false);
      })
  }

  return (
    <div className="upload">
      <h2>Upload Data</h2>

      <div className="upload-form">
        <div className="form-group">
          <label>Data Source</label>
          <select value={sourceType} onChange={e => setSourceType(e.target.value)}>
            <option value="SAP">SAP — Fuel & Procurement</option>
            <option value="UTILITY">Utility — Electricity</option>
            <option value="TRAVEL">Travel — Concur Export</option>
          </select>
        </div>

        <div className="form-group">
          <label>CSV File</label>
          <input type="file" accept=".csv" onChange={e => setFile(e.target.files[0])} />
        </div>

        <button className="btn-upload" onClick={upload} disabled={loading}>
          {loading ? "Uploading..." : "Upload & Ingest"}
        </button>

        {result && (
          <div className="success-box">
            <p>✓ Batch ID: {result.batch_id}</p>
            <p>✓ Rows processed: {result.rows_processed}</p>
            <p>✓ Errors: {result.errors}</p>
            <p>{result.message}</p>
          </div>
        )}

        {error && <div className="error-box">{error}</div>}
      </div>
    </div>
  )
}