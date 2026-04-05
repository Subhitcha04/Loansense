import { useEffect, useState } from 'react'
import { getApplications, createApplicant, submitApplication } from '../api/client.js'
import ApplicationsTable from '../components/ApplicationsTable.jsx'

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label className="field-label">{label}</label>
      {children}
    </div>
  )
}

function Modal({ onClose, onSuccess }) {
  const [step,      setStep]      = useState(1)
  const [appId,     setAppId]     = useState(null)
  const [loading,   setLoading]   = useState(false)
  const [applicant, setApplicant] = useState({
    name: '', email: '', income: '', employment_years: '',
    existing_loans: '0', debt_to_income: '', credit_history_years: '',
  })
  const [loan, setLoan] = useState({ amount: '', term_months: '24', purpose: 'personal' })

  const setA = (k, v) => setApplicant(p => ({ ...p, [k]: v }))
  const setL = (k, v) => setLoan(p => ({ ...p, [k]: v }))

  async function next() {
    setLoading(true)
    try {
      const res = await createApplicant({
        name: applicant.name, email: applicant.email,
        income: +applicant.income, employment_years: +applicant.employment_years,
        existing_loans: +applicant.existing_loans, debt_to_income: +applicant.debt_to_income,
        credit_history_years: +applicant.credit_history_years,
      })
      setAppId(res.data.id)
      setStep(2)
    } catch (e) {
      alert(e.response?.data?.detail || 'Error creating applicant')
    } finally { setLoading(false) }
  }

  async function submit() {
    setLoading(true)
    try {
      await submitApplication({ applicant_id: appId, amount: +loan.amount, term_months: +loan.term_months, purpose: loan.purpose })
      onSuccess()
    } catch (e) {
      alert(e.response?.data?.detail || 'Error submitting application')
    } finally { setLoading(false) }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200, background: 'rgba(0,0,0,0.7)' }}>
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', width: 460, maxHeight: '90vh', overflow: 'auto' }}>
        {/* Header */}
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-muted)', marginBottom: 2 }}>
              STEP {step} OF 2
            </div>
            <div style={{ fontWeight: 600 }}>
              {step === 1 ? 'Applicant Details' : 'Loan Parameters'}
            </div>
          </div>
          <button className="btn btn-ghost" onClick={onClose} style={{ padding: '6px 8px' }}>&#x2715;</button>
        </div>

        {/* Progress */}
        <div style={{ display: 'flex', gap: 4, padding: '0 24px', marginTop: -1 }}>
          {[1,2].map(s => (
            <div key={s} style={{ flex: 1, height: 2, background: s <= step ? 'var(--accent)' : 'var(--border)' }} />
          ))}
        </div>

        <div style={{ padding: '24px' }}>
          {step === 1 ? (
            <>
              <Field label="Full Name">
                <input placeholder="Priya Venkataraman" value={applicant.name} onChange={e => setA('name', e.target.value)} />
              </Field>
              <Field label="Email Address">
                <input type="email" placeholder="priya@example.com" value={applicant.email} onChange={e => setA('email', e.target.value)} />
              </Field>
              <div className="grid-2">
                <Field label="Annual Income (₹)">
                  <input type="number" placeholder="600000" value={applicant.income} onChange={e => setA('income', e.target.value)} />
                </Field>
                <Field label="Employment Years">
                  <input type="number" placeholder="5" value={applicant.employment_years} onChange={e => setA('employment_years', e.target.value)} />
                </Field>
              </div>
              <div className="grid-2">
                <Field label="Debt-to-Income Ratio">
                  <input type="number" placeholder="0.30" step="0.01" value={applicant.debt_to_income} onChange={e => setA('debt_to_income', e.target.value)} />
                </Field>
                <Field label="Existing Loans">
                  <input type="number" placeholder="0" value={applicant.existing_loans} onChange={e => setA('existing_loans', e.target.value)} />
                </Field>
              </div>
              <Field label="Credit History (Years)">
                <input type="number" placeholder="7" value={applicant.credit_history_years} onChange={e => setA('credit_history_years', e.target.value)} />
              </Field>
              <button className="btn btn-primary" style={{ width: '100%' }} onClick={next} disabled={loading}>
                {loading ? 'Creating applicant...' : 'Continue'}
              </button>
            </>
          ) : (
            <>
              <Field label="Loan Amount (₹)">
                <input type="number" placeholder="500000" value={loan.amount} onChange={e => setL('amount', e.target.value)} />
              </Field>
              <div className="grid-2">
                <Field label="Term (Months)">
                  <select value={loan.term_months} onChange={e => setL('term_months', e.target.value)}>
                    {[6,12,18,24,36,48,60].map(t => <option key={t} value={t}>{t}m</option>)}
                  </select>
                </Field>
                <Field label="Purpose">
                  <select value={loan.purpose} onChange={e => setL('purpose', e.target.value)}>
                    {['education','personal','medical','business'].map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </Field>
              </div>
              <div style={{ background: 'var(--surface2)', borderRadius: 'var(--radius)', padding: '12px 14px', marginBottom: 20, fontSize: 12, color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
                ML risk scoring will run automatically after submission.
                Interest rate (8.5–18%) is assigned based on the model output.
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button className="btn btn-outline" onClick={() => setStep(1)} style={{ flex: '0 0 auto' }}>Back</button>
                <button className="btn btn-primary" style={{ flex: 1 }} onClick={submit} disabled={loading}>
                  {loading ? 'Submitting...' : 'Submit Application'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Applications() {
  const [applications, setApplications] = useState([])
  const [loading,      setLoading]      = useState(true)
  const [showModal,    setShowModal]    = useState(false)

  function load() {
    setLoading(true)
    getApplications().then(r => setApplications(r.data)).catch(console.error).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h1>Applications</h1>
            <p>{applications.length} records &mdash; click any row to review and decide</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>New Application</button>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading">Loading...</div>
        ) : applications.length === 0 ? (
          <div className="empty">No applications yet. Submit the first one.</div>
        ) : (
          <ApplicationsTable applications={applications} onRefresh={load} />
        )}
      </div>

      {showModal && <Modal onClose={() => setShowModal(false)} onSuccess={() => { load(); setShowModal(false) }} />}
    </div>
  )
}
