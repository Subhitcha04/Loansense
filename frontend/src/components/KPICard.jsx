export default function KPICard({ title, value, sub, accent = false }) {
  return (
    <div className="card" style={{ position: 'relative' }}>
      <div className="stat-label">{title}</div>
      <div className="stat-value" style={accent ? { color: 'var(--accent)' } : {}}>
        {value}
      </div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}
