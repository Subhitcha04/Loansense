import { useState } from 'react'
import { RiskScoreBar, RiskBadge, StatusBadge } from './RiskScoreBadge.jsx'
import { makeDecision } from '../api/client.js'

function Drawer({ app, onClose, onDecision }) {
  const [loading, setLoading] = useState(false)

  async function decide(decision) {
    setLoading(true)
    try {
      await makeDecision(app.id, { decision })
      onDecision()
      onClose()
    } catch (e) {
      alert(e.response?.data?.detail || 'Decision failed')
    } finally {
      setLoading(false)
    }
  }

  const fi = app.feature_importances || {}
  const fiEntries = Object.entries(fi).sort((a, b) => b[1] - a[1]).slice(0, 8)

  const row = (label, value) => (
    <div key={label} style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '9px 0', borderBottom: '1px solid var(--border)',
    }}>
      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ fontSize: 13 }}>{value}</span>
    </div>
  )

  return (
    <div style={{
      position: 'fixed', top: 0, right: 0, bottom: 0, width: 380,
      background: 'var(--surface)', borderLeft: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column', zIndex: 100,
    }}>
      {/* Header */}
      <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>APPLICATION</div>
          <div style={{ fontWeight: 600, fontSize: 16 }}>#{app.id}</div>
        </div>
        <button className="btn btn-ghost" onClick={onClose} style={{ padding: '6px 8px', fontSize: 16 }}>
          &#x2715;
        </button>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 24px' }}>
        <div style={{ paddingTop: 16, paddingBottom: 20 }}>
          {row('Applicant', app.applicant_name || `Applicant #${app.applicant_id}`)}
          {row('Amount', `₹${Number(app.amount).toLocaleString('en-IN')}`)}
          {row('Term', `${app.term_months} months`)}
          {row('Purpose', <span style={{ textTransform: 'capitalize' }}>{app.purpose}</span>)}
          {row('Status', <StatusBadge status={app.status} />)}
          {row('Risk Tier', <RiskBadge tier={app.risk_tier} />)}
          {row('Interest Rate', app.interest_rate ? `${app.interest_rate}% p.a.` : '—')}
          {row('Recommendation', app.recommended_action
            ? <span style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>{app.recommended_action}</span>
            : '—')}
        </div>

        {/* Risk score */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: 10 }}>
            Risk Score
          </div>
          <RiskScoreBar score={app.risk_score} />
        </div>

        {/* Feature importances */}
        {fiEntries.length > 0 && (
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 11, fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)', marginBottom: 12 }}>
              Feature Importances
            </div>
            {fiEntries.map(([feat, imp]) => (
              <div key={feat} style={{ marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{feat}</span>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                    {(imp * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={{ height: 2, background: 'var(--surface3)', borderRadius: 1 }}>
                  <div style={{ width: `${imp * 100}%`, height: '100%', background: 'var(--accent)', borderRadius: 1 }} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Decision */}
      {app.status === 'pending' && (
        <div style={{ padding: '20px 24px', borderTop: '1px solid var(--border)', display: 'flex', gap: 10 }}>
          <button className="btn btn-confirm" style={{ flex: 1 }} onClick={() => decide('approved')} disabled={loading}>
            Approve
          </button>
          <button className="btn btn-danger" style={{ flex: 1 }} onClick={() => decide('rejected')} disabled={loading}>
            Reject
          </button>
        </div>
      )}
    </div>
  )
}

export default function ApplicationsTable({ applications, onRefresh }) {
  const [selected, setSelected] = useState(null)

  return (
    <div style={{ overflowX: 'auto' }}>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Applicant</th>
            <th>Amount</th>
            <th>Purpose</th>
            <th>Risk Score</th>
            <th>Tier</th>
            <th>Status</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {applications.map(app => (
            <tr key={app.id} onClick={() => setSelected(app)}
              style={{ cursor: 'pointer' }}>
              <td><span className="chip">#{app.id}</span></td>
              <td style={{ fontWeight: 500, color: 'var(--text)' }}>
                {app.applicant_name || `Applicant #${app.applicant_id}`}
              </td>
              <td style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>
                ₹{Number(app.amount).toLocaleString('en-IN')}
              </td>
              <td style={{ textTransform: 'capitalize', color: 'var(--text-secondary)' }}>
                {app.purpose}
              </td>
              <td style={{ minWidth: 130 }}>
                <RiskScoreBar score={app.risk_score} />
              </td>
              <td><RiskBadge tier={app.risk_tier} /></td>
              <td><StatusBadge status={app.status} /></td>
              <td style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                {new Date(app.created_at).toLocaleDateString('en-IN')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {selected && (
        <>
          <div onClick={() => setSelected(null)} style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 99,
          }} />
          <Drawer app={selected} onClose={() => setSelected(null)} onDecision={() => { setSelected(null); onRefresh() }} />
        </>
      )}
    </div>
  )
}
