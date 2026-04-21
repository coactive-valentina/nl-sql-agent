import { useState, useEffect } from 'react'

const API_URL = 'http://127.0.0.1:8000'
const DEFAULT_DATASET_ID = 'bb909094-21ba-49b4-863f-ac5edb9af0b6'

// --- Header ---
function Header() {
  return (
    <header style={{
      backgroundColor: 'var(--green-dark)',
      padding: '16px 32px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
    }}>
      <img src="/coactive-logo.jpg" alt="Coactive" style={{ height: '32px' }} />
      <div style={{ color: 'var(--green-light)', fontSize: '13px', opacity: 0.8, borderLeft: '1px solid rgba(255,255,255,0.2)', paddingLeft: '12px' }}>
        NL-SQL Agent
      </div>
    </header>
  )
}

// --- SQL Display ---
function SQLDisplay({ sql }) {
  if (!sql) return null
  return (
    <div style={{ marginTop: '24px' }}>
      <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--gray-600)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Generated SQL
      </div>
      <pre style={{
        backgroundColor: 'var(--green-dark)',
        color: 'var(--green-medium)',
        padding: '16px',
        borderRadius: 'var(--radius)',
        fontSize: '13px',
        overflowX: 'auto',
        lineHeight: '1.6',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}>
        {sql}
      </pre>
    </div>
  )
}

// --- Results Table ---
function ResultsTable({ results }) {
  if (!results || results.length === 0) return null
  const columns = Object.keys(results[0])

  return (
    <div style={{ marginTop: '24px' }}>
      <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--gray-600)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Results ({results.length} row{results.length !== 1 ? 's' : ''})
      </div>
      <div style={{ overflowX: 'auto', borderRadius: 'var(--radius)', border: '1px solid var(--gray-200)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ backgroundColor: 'var(--green-light)' }}>
              {columns.map(col => (
                <th key={col} style={{
                  padding: '10px 16px',
                  textAlign: 'left',
                  fontWeight: 600,
                  color: 'var(--green-dark)',
                  borderBottom: '2px solid var(--green-medium)',
                  whiteSpace: 'nowrap',
                }}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.map((row, i) => (
              <tr key={i} style={{ backgroundColor: i % 2 === 0 ? 'var(--white)' : 'var(--gray-100)' }}>
                {columns.map(col => (
                  <td key={col} style={{
                    padding: '10px 16px',
                    borderBottom: '1px solid var(--gray-200)',
                    color: 'var(--gray-900)',
                    maxWidth: '300px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {String(row[col] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// --- Query Panel ---
function QueryPanel() {
  const [question, setQuestion] = useState('')
  const [datasetId, setDatasetId] = useState(DEFAULT_DATASET_ID)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async () => {
    if (!question.trim()) return
    setLoading(true)
    setResult(null)
    setError(null)

    try {
      const res = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, dataset_id: datasetId }),
      })
      const data = await res.json()
      if (data.error) {
        setError(data.error)
      } else {
        setResult(data)
      }
    } catch (e) {
      setError('Failed to connect to the backend. Is the server running?')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit()
  }

  return (
    <div style={{
      backgroundColor: 'var(--white)',
      borderRadius: 'var(--radius)',
      padding: '28px',
      boxShadow: 'var(--shadow)',
    }}>
      <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--green-dark)', marginBottom: '20px' }}>
        Ask a Question
      </h2>

      {/* Dataset ID */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--gray-600)', marginBottom: '6px' }}>
          Dataset ID
        </label>
        <input
          type="text"
          value={datasetId}
          onChange={e => setDatasetId(e.target.value)}
          style={{
            width: '100%',
            padding: '10px 14px',
            border: '1px solid var(--gray-200)',
            borderRadius: 'var(--radius)',
            fontSize: '14px',
            fontFamily: 'monospace',
            color: 'var(--gray-600)',
            outline: 'none',
          }}
        />
      </div>

      {/* Question Input */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--gray-600)', marginBottom: '6px' }}>
          Natural Language Question <span style={{ color: 'var(--gray-600)', fontWeight: 400 }}>(Cmd+Enter to submit)</span>
        </label>
        <textarea
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. How many distinct videos are in the dataset?"
          rows={3}
          style={{
            width: '100%',
            padding: '10px 14px',
            border: '1px solid var(--gray-200)',
            borderRadius: 'var(--radius)',
            fontSize: '14px',
            resize: 'vertical',
            outline: 'none',
            lineHeight: '1.5',
          }}
        />
      </div>

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={loading || !question.trim()}
        style={{
          backgroundColor: loading || !question.trim() ? 'var(--gray-200)' : 'var(--green-primary)',
          color: loading || !question.trim() ? 'var(--gray-600)' : 'var(--white)',
          border: 'none',
          borderRadius: 'var(--radius)',
          padding: '10px 24px',
          fontSize: '14px',
          fontWeight: 600,
          cursor: loading || !question.trim() ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.2s',
        }}
      >
        {loading ? 'Running query...' : 'Run Query'}
      </button>

      {/* Error */}
      {error && (
        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          backgroundColor: '#fef2f2',
          border: '1px solid var(--red)',
          borderRadius: 'var(--radius)',
          color: 'var(--red)',
          fontSize: '14px',
        }}>
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          <SQLDisplay sql={result.sql} />
          <ResultsTable results={result.results} />
        </>
      )}
    </div>
  )
}

// --- Logs Panel ---
function LogsPanel() {
  const [logs, setLogs] = useState([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/logs`)
      const data = await res.json()
      setLogs(data.logs.reverse())
    } catch {
      setLogs([])
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = () => {
    if (!open) fetchLogs()
    setOpen(o => !o)
  }

  return (
    <div style={{
      backgroundColor: 'var(--white)',
      borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow)',
      overflow: 'hidden',
    }}>
      {/* Toggle Header */}
      <button
        onClick={handleToggle}
        style={{
          width: '100%',
          padding: '16px 28px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: 'var(--white)',
          border: 'none',
          cursor: 'pointer',
          fontSize: '16px',
          fontWeight: 700,
          color: 'var(--green-dark)',
        }}
      >
        Interaction Logs
        <span style={{ fontSize: '12px', color: 'var(--gray-600)', fontWeight: 400 }}>
          {open ? '▲ Hide' : '▼ Show'}
        </span>
      </button>

      {open && (
        <div style={{ padding: '0 28px 28px' }}>
          {loading ? (
            <div style={{ color: 'var(--gray-600)', fontSize: '14px' }}>Loading logs...</div>
          ) : logs.length === 0 ? (
            <div style={{ color: 'var(--gray-600)', fontSize: '14px' }}>No interactions logged yet.</div>
          ) : (
            <div style={{ overflowX: 'auto', borderRadius: 'var(--radius)', border: '1px solid var(--gray-200)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ backgroundColor: 'var(--green-light)' }}>
                    {['Timestamp', 'Question', 'Result Count', 'Error'].map(h => (
                      <th key={h} style={{
                        padding: '10px 16px',
                        textAlign: 'left',
                        fontWeight: 600,
                        color: 'var(--green-dark)',
                        borderBottom: '2px solid var(--green-medium)',
                        whiteSpace: 'nowrap',
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log, i) => (
                    <tr key={i} style={{ backgroundColor: i % 2 === 0 ? 'var(--white)' : 'var(--gray-100)' }}>
                      <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--gray-200)', whiteSpace: 'nowrap', color: 'var(--gray-600)' }}>
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--gray-200)', maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {log.question}
                      </td>
                      <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--gray-200)', textAlign: 'center' }}>
                        {log.result_count}
                      </td>
                      <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--gray-200)', color: log.error ? 'var(--red)' : 'var(--green-primary)' }}>
                        {log.error ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// --- App ---
export default function App() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header />
      <main style={{ flex: 1, maxWidth: '900px', width: '100%', margin: '0 auto', padding: '32px 16px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <QueryPanel />
        <LogsPanel />
      </main>
      <footer style={{ textAlign: 'center', padding: '16px', fontSize: '12px', color: 'var(--gray-600)' }}>
        Coactive NL-SQL Agent — Powered by OpenAI GPT-4o
      </footer>
    </div>
  )
}