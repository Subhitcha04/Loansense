import { useState } from 'react'
import { makePayment } from '../api/client.js'

export default function RepaymentTracker({ schedule, loanId, onRefresh }) {
  const [paying, setPaying] = useState(false)

  async function pay() {
    setPaying(true)
    try {
      await makePayment(loanId)
      onRefresh()
    } catch (e) {
      alert(e.response?.data?.detail || 'Payment failed')
    } finally {
      setPaying(false)
    }
  }

  const paid    = schedule.filter(r => r.status === 'paid').length
  const overdue = schedule.filter(r => r.status === 'overdue').length
  const upcoming= schedule.filter(r => r.status === 'upcoming').length
  const total   = schedule.length
  const hasUnpaid = schedule.some(r => r.status !== 'paid')

  return (
    <div>
      {/* Summary strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 24 }}>
        {[
          ['Total', total,   'var(--text-secondary)'],
          ['Paid',    paid,    'var(--green)'],
          ['Upcoming',upcoming,'var(--accent)'],
          ['Overdue', overdue, 'var(--red)'],
        ].map(([label, count, color]) => (
          <div key={label} style={{ background: 'var(--surface2)', borderRadius: 'var(--radius)', padding: '12px 16px', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 20, fontWeight: 600, color, fontFamily: 'var(--mono)' }}>{count}</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px', marginTop: 3 }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Progress */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 6 }}>
          <span style={{ color: 'var(--text-muted)' }}>Repayment progress</span>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-secondary)' }}>
            {paid}/{total}
          </span>
        </div>
        <div style={{ height: 4, background: 'var(--surface3)', borderRadius: 2 }}>
          <div style={{
            height: '100%', borderRadius: 2, background: 'var(--accent)',
            width: `${total ? (paid / total) * 100 : 0}%`, transition: 'width 0.3s',
          }} />
        </div>
      </div>

      {hasUnpaid && (
        <div style={{ marginBottom: 20 }}>
          <button className="btn btn-primary" onClick={pay} disabled={paying}>
            {paying ? 'Processing...' : 'Record Next Payment'}
          </button>
        </div>
      )}

      <div style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Due Date</th>
              <th>EMI</th>
              <th>Principal</th>
              <th>Interest</th>
              <th>Balance</th>
              <th>Status</th>
              <th>Paid On</th>
            </tr>
          </thead>
          <tbody>
            {schedule.map(r => {
              const rowBg =
                r.status === 'paid'    ? 'rgba(34,197,94,0.04)'  :
                r.status === 'overdue' ? 'rgba(239,68,68,0.04)'  : 'transparent'
              const statusColor =
                r.status === 'paid'    ? 'var(--green)' :
                r.status === 'overdue' ? 'var(--red)'   : 'var(--text-muted)'
              return (
                <tr key={r.instalment_no} style={{ background: rowBg }}>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>{r.instalment_no}</td>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>{r.due_date}</td>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 12, fontWeight: 500, color: 'var(--text)' }}>
                    ₹{Number(r.emi_amount).toLocaleString('en-IN')}
                  </td>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>
                    ₹{Number(r.principal_component).toLocaleString('en-IN')}
                  </td>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--amber)' }}>
                    ₹{Number(r.interest_component).toLocaleString('en-IN')}
                  </td>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>
                    ₹{Number(r.outstanding_balance).toLocaleString('en-IN')}
                  </td>
                  <td>
                    <span style={{ fontSize: 11, fontFamily: 'var(--mono)', color: statusColor }}>
                      {r.status}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                    {r.paid_on || '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
