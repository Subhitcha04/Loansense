export function RiskScoreBar({ score }) {
  if (score == null) return (
    <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--mono)', fontSize: 12 }}>
      scoring...
    </span>
  )
  const pct = Math.round(score * 100)
  const color = score < 0.3 ? 'var(--green)' : score < 0.6 ? 'var(--amber)' : 'var(--red)'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 120 }}>
      <div style={{ flex: 1, height: 3, background: 'var(--surface3)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 2 }} />
      </div>
      <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color, minWidth: 26, textAlign: 'right' }}>
        {pct}%
      </span>
    </div>
  )
}

export function RiskBadge({ tier }) {
  if (!tier) return <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>—</span>
  return <span className={`badge badge-${tier}`}>{tier}</span>
}

export function StatusBadge({ status }) {
  if (!status) return null
  return <span className={`badge badge-${status}`}>{status}</span>
}
