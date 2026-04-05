import { useEffect, useState } from 'react'
import { getLoans, getLoanSchedule, getLoanStatus } from '../api/client.js'
import RepaymentTracker from '../components/RepaymentTracker.jsx'
import { StatusBadge } from '../components/RiskScoreBadge.jsx'

export default function Loans() {
  const [loans,           setLoans]           = useState([])
  const [selected,        setSelected]        = useState(null)
  const [schedule,        setSchedule]        = useState([])
  const [loanStatus,      setLoanStatus]      = useState(null)
  const [loading,         setLoading]         = useState(true)
  const [scheduleLoading, setScheduleLoading] = useState(false)
  const [search,          setSearch]          = useState('')

  useEffect(() => {
    getLoans().then(r => setLoans(r.data)).catch(console.error).finally(() => setLoading(false))
  }, [])

  async function selectLoan(loan) {
    setSelected(loan)
    setScheduleLoading(true)
    try {
      const [s, st] = await Promise.all([getLoanSchedule(loan.id), getLoanStatus(loan.id)])
      setSchedule(s.data)
      setLoanStatus(st.data)
    } catch (e) { console.error(e) }
    finally { setScheduleLoading(false) }
  }

  function refresh() { if (selected) selectLoan(selected) }

  const filtered = loans.filter(l =>
    String(l.id).includes(search) ||
    (l.applicant_name || '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="page">
      <div className="page-header">
        <h1>Loans</h1>
        <p>Select a loan to view its full amortisation schedule</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 16, alignItems: 'start' }}>
        {/* Loan list */}
        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
            <input placeholder="Search by ID or name..." value={search}
              onChange={e => setSearch(e.target.value)} />
          </div>
          <div style={{ maxHeight: 'calc(100vh - 220px)', overflowY: 'auto' }}>
            {loading ? (
              <div className="loading" style={{ padding: 40, fontSize: 12 }}>Loading...</div>
            ) : filtered.length === 0 ? (
              <div className="empty" style={{ padding: 32, fontSize: 12 }}>No loans found</div>
            ) : filtered.map(loan => (
              <div key={loan.id} onClick={() => selectLoan(loan)} style={{
                padding: '14px 16px', cursor: 'pointer',
                borderBottom: '1px solid var(--border)',
                borderLeft: selected?.id === loan.id ? '2px solid var(--accent)' : '2px solid transparent',
                background: selected?.id === loan.id ? 'var(--surface2)' : 'transparent',
                transition: 'background 0.1s',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                    #{loan.id}
                  </span>
                  <StatusBadge status={loan.status} />
                </div>
                <div style={{ fontWeight: 500, fontSize: 13, marginBottom: 3 }}>
                  {loan.applicant_name || `Applicant #${loan.applicant_id}`}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                  <span style={{ fontFamily: 'var(--mono)', color: 'var(--text)' }}>
                    ₹{Number(loan.principal).toLocaleString('en-IN')}
                  </span>
                  <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--mono)' }}>
                    {loan.interest_rate}% · {loan.term_months}m
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Schedule */}
        <div className="card">
          {!selected ? (
            <div className="empty" style={{ padding: 100 }}>
              Select a loan from the list to view its repayment schedule
            </div>
          ) : scheduleLoading ? (
            <div className="loading">Loading schedule...</div>
          ) : (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24, paddingBottom: 20, borderBottom: '1px solid var(--border)' }}>
                <div>
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-muted)', marginBottom: 4 }}>LOAN #{selected.id}</div>
                  <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 4 }}>
                    {selected.applicant_name || `Applicant #${selected.applicant_id}`}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    ₹{Number(selected.principal).toLocaleString('en-IN')} &nbsp;&middot;&nbsp;
                    {selected.interest_rate}% p.a. &nbsp;&middot;&nbsp;
                    {selected.term_months} months
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 20, fontWeight: 500 }}>
                    ₹{Number(selected.emi_amount).toLocaleString('en-IN')}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>per month</div>
                </div>
              </div>

              {loanStatus?.overdue_instalments > 0 && (
                <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 'var(--radius)', padding: '10px 14px', marginBottom: 20, fontSize: 12, color: 'var(--red)' }}>
                  {loanStatus.overdue_instalments} instalment(s) overdue — next due {loanStatus.next_due_date}
                </div>
              )}

              <RepaymentTracker schedule={schedule} loanId={selected.id} onRefresh={refresh} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
