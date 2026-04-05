import { useEffect, useState } from 'react'
import { getWebhookEvents, getEndpoints, registerWebhook, deleteEndpoint } from '../api/client.js'
import WebhookEventLog from '../components/WebhookEventLog.jsx'

const EVENTS = [
  { event: 'application.scored', desc: 'ML scoring complete' },
  { event: 'loan.approved',      desc: 'Application approved' },
  { event: 'loan.rejected',      desc: 'Application rejected' },
  { event: 'payment.received',   desc: 'EMI recorded' },
  { event: 'payment.overdue',    desc: 'Instalment past due' },
]

export default function Webhooks() {
  const [events,    setEvents]    = useState([])
  const [endpoints, setEndpoints] = useState([])
  const [url,       setUrl]       = useState('')
  const [desc,      setDesc]      = useState('')
  const [loading,   setLoading]   = useState(false)

  function load() {
    Promise.all([getWebhookEvents(), getEndpoints()])
      .then(([ev, ep]) => { setEvents(ev.data); setEndpoints(ep.data) })
      .catch(console.error)
  }
  useEffect(() => { load() }, [])

  async function register() {
    if (!url) return
    setLoading(true)
    try {
      await registerWebhook({ url, description: desc })
      setUrl(''); setDesc(''); load()
    } catch (e) {
      alert(e.response?.data?.detail || 'Registration failed')
    } finally { setLoading(false) }
  }

  async function remove(id) { await deleteEndpoint(id); load() }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Webhooks</h1>
        <p>Event delivery with exponential backoff retry: 0s &rarr; 5min &rarr; 30min</p>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        {/* Register */}
        <div className="card">
          <div className="card-title">Register Endpoint</div>
          <div style={{ marginBottom: 14 }}>
            <label className="field-label">URL</label>
            <input placeholder="https://your-system.com/webhook" value={url} onChange={e => setUrl(e.target.value)} />
          </div>
          <div style={{ marginBottom: 20 }}>
            <label className="field-label">Description</label>
            <input placeholder="e.g. CRM notifications" value={desc} onChange={e => setDesc(e.target.value)} />
          </div>
          <button className="btn btn-primary" onClick={register} disabled={loading || !url}>
            {loading ? 'Registering...' : 'Register'}
          </button>
        </div>

        {/* Event types */}
        <div className="card">
          <div className="card-title">Event Types</div>
          <table>
            <tbody>
              {EVENTS.map(({ event, desc }) => (
                <tr key={event}>
                  <td style={{ paddingLeft: 0 }}>
                    <span className="chip">{event}</span>
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Endpoints */}
      {endpoints.length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-title">Active Endpoints ({endpoints.length})</div>
          <table>
            <thead>
              <tr>
                <th>URL</th>
                <th>Description</th>
                <th>Registered</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {endpoints.map(ep => (
                <tr key={ep.id}>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>{ep.url}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{ep.description || '—'}</td>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                    {new Date(ep.created_at).toLocaleDateString('en-IN')}
                  </td>
                  <td>
                    <button className="btn btn-outline" style={{ fontSize: 11, padding: '4px 10px' }}
                      onClick={() => remove(ep.id)}>Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Event log */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div className="card-title" style={{ marginBottom: 0 }}>Delivery Log</div>
          <button className="btn btn-ghost" style={{ fontSize: 12 }} onClick={load}>Refresh</button>
        </div>
        <WebhookEventLog events={events} />
      </div>
    </div>
  )
}
