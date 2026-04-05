import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard    from './pages/Dashboard.jsx'
import Applications from './pages/Applications.jsx'
import Loans        from './pages/Loans.jsx'
import Webhooks     from './pages/Webhooks.jsx'

const NAV = [
  { to: '/',             label: 'Overview' },
  { to: '/applications', label: 'Applications' },
  { to: '/loans',        label: 'Loans' },
  { to: '/webhooks',     label: 'Webhooks' },
]

const SidebarIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <rect x="2" y="2" width="7" height="7" rx="1.5" fill="var(--accent)" />
    <rect x="11" y="2" width="7" height="7" rx="1.5" fill="var(--accent)" opacity="0.4" />
    <rect x="2" y="11" width="7" height="7" rx="1.5" fill="var(--accent)" opacity="0.4" />
    <rect x="11" y="11" width="7" height="7" rx="1.5" fill="var(--accent)" opacity="0.7" />
  </svg>
)

function Sidebar() {
  return (
    <aside style={{
      width: 200, minHeight: '100vh',
      background: 'var(--surface)',
      borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      position: 'fixed', top: 0, left: 0, zIndex: 50,
    }}>
      {/* Brand */}
      <div style={{ padding: '20px 20px 16px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <SidebarIcon />
          <div>
            <div style={{ fontWeight: 600, fontSize: 14, letterSpacing: '-0.2px' }}>LoanSense</div>
            <div style={{ color: 'var(--text-muted)', fontSize: 10, fontFamily: 'var(--mono)', marginTop: 1 }}>v1.0</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '12px 8px' }}>
        <div style={{ fontSize: 10, fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.6px', color: 'var(--text-muted)', padding: '4px 12px 8px' }}>
          Platform
        </div>
        {NAV.map(({ to, label }) => (
          <NavLink key={to} to={to} end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center',
              padding: '8px 12px', borderRadius: 'var(--radius)',
              fontSize: 13, fontWeight: isActive ? 500 : 400,
              color: isActive ? 'var(--text)' : 'var(--text-secondary)',
              background: isActive ? 'var(--surface2)' : 'transparent',
              marginBottom: 2, transition: 'all 0.1s',
              borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
            })}
          >
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)' }}>
        <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer"
          style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)',
            fontFamily: 'var(--mono)', transition: 'color 0.1s' }}
          onMouseOver={e => e.target.style.color = 'var(--accent)'}
          onMouseOut={e => e.target.style.color = 'var(--text-muted)'}
        >
          API Docs /docs
        </a>
        <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4, fontWeight: 300 }}>
          FastAPI · React · MySQL
        </div>
      </div>
    </aside>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex' }}>
        <Sidebar />
        <main style={{ marginLeft: 200, flex: 1, minHeight: '100vh' }}>
          <Routes>
            <Route path="/"             element={<Dashboard />} />
            <Route path="/applications" element={<Applications />} />
            <Route path="/loans"        element={<Loans />} />
            <Route path="/webhooks"     element={<Webhooks />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
