import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend,
} from 'recharts'
import KPICard from '../components/KPICard.jsx'
import { getPortfolio, getRiskDistribution, getRepaymentTrends } from '../api/client.js'

const TIER_COLORS = { low: '#22c55e', medium: '#f59e0b', high: '#ef4444' }
const fmt = n => `₹${(n / 100000).toFixed(1)}L`

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '10px 14px', fontSize: 12, fontFamily: 'var(--mono)' }}>
      {label && <div style={{ color: 'var(--text-muted)', marginBottom: 6 }}>{label}</div>}
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color || 'var(--text)', marginTop: 3 }}>
          {p.name}: {typeof p.value === 'number' && p.value > 10000 ? fmt(p.value) : p.value}
        </div>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [portfolio,     setPortfolio]     = useState(null)
  const [distribution,  setDistribution]  = useState(null)
  const [trends,        setTrends]        = useState(null)
  const [loading,       setLoading]       = useState(true)

  useEffect(() => {
    Promise.all([getPortfolio(), getRiskDistribution(), getRepaymentTrends()])
      .then(([p, d, t]) => { setPortfolio(p.data); setDistribution(d.data); setTrends(t.data) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading...</div>
  if (!portfolio) return <div className="loading">API unavailable. Is the backend running?</div>

  const pieData = (distribution?.distribution || []).map(d => ({
    name: d.tier.charAt(0).toUpperCase() + d.tier.slice(1),
    value: d.count, tier: d.tier,
  }))

  const weeklyData = (portfolio.weekly_disbursements || []).map(w => ({
    week: `W${String(w.week).slice(-2)}`, loans: w.count, amount: w.total,
  }))

  const trendData = (trends?.trends || []).map(t => ({
    month: t.month,
    Expected: Math.round(t.expected),
    Collected: Math.round(t.collected),
  }))

  return (
    <div className="page">
      <div className="page-header">
        <h1>Portfolio Overview</h1>
        <p>Aggregate metrics across the active loan portfolio</p>
      </div>

      {/* KPIs */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        <KPICard
          title="Total Disbursed"
          value={fmt(portfolio.total_disbursed)}
          sub={`${portfolio.total_loans} loans`}
        />
        <KPICard
          title="Active Loans"
          value={portfolio.active_loans}
          sub={`${portfolio.closed_loans} closed`}
        />
        <KPICard
          title="Collection Rate"
          value={`${portfolio.collection_rate}%`}
          sub="This month"
          accent
        />
        <KPICard
          title="Default Rate"
          value={`${portfolio.default_rate}%`}
          sub={`Avg risk score ${(portfolio.average_risk_score * 100).toFixed(0)}%`}
        />
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Weekly disbursements */}
        <div className="card">
          <div className="card-title">Weekly Disbursements</div>
          {weeklyData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={weeklyData} barSize={24}>
                <CartesianGrid strokeDasharray="2 4" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="week" tick={{ fill: 'var(--text-muted)', fontSize: 11, fontFamily: 'var(--mono)' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11, fontFamily: 'var(--mono)' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="loans" fill="var(--accent)" radius={[3, 3, 0, 0]} name="Loans" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty" style={{ padding: 40 }}>No disbursement data yet</div>
          )}
        </div>

        {/* Risk tier pie */}
        <div className="card">
          <div className="card-title">Portfolio by Risk Tier</div>
          {pieData.length > 0 ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
              <ResponsiveContainer width="60%" height={200}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80}
                    dataKey="value" paddingAngle={2}>
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={TIER_COLORS[entry.tier]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ flex: 1 }}>
                {pieData.map(d => (
                  <div key={d.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: TIER_COLORS[d.tier.toLowerCase()] }} />
                      <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{d.name}</span>
                    </div>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 13 }}>{d.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty" style={{ padding: 40 }}>No approved loans yet</div>
          )}
        </div>
      </div>

      {/* Repayment trends */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title">Repayment Trends — Last 6 Months</div>
        {trendData.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="2 4" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="month" tick={{ fill: 'var(--text-muted)', fontSize: 11, fontFamily: 'var(--mono)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11, fontFamily: 'var(--mono)' }} axisLine={false} tickLine={false} tickFormatter={v => `₹${(v/1000).toFixed(0)}K`} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'var(--mono)', paddingTop: 12 }} />
              <Line type="monotone" dataKey="Expected" stroke="var(--border-light)" strokeWidth={1.5} dot={false} strokeDasharray="4 3" />
              <Line type="monotone" dataKey="Collected" stroke="var(--accent)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty" style={{ padding: 40 }}>No repayment data yet</div>
        )}
      </div>

      {/* By purpose */}
      {portfolio.disbursement_by_purpose?.length > 0 && (
        <div className="card">
          <div className="card-title">Disbursement by Purpose</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12 }}>
            {portfolio.disbursement_by_purpose.map(p => (
              <div key={p.purpose} style={{ background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '16px' }}>
                <div style={{ fontFamily: 'var(--mono)', fontSize: 18, fontWeight: 500 }}>{p.count}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'capitalize', marginTop: 3 }}>{p.purpose}</div>
                <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--accent)', marginTop: 8 }}>{fmt(p.total)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
