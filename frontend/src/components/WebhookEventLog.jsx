export default function WebhookEventLog({ events }) {
  if (!events.length) return (
    <div className="empty">No webhook events recorded yet.</div>
  )
  return (
    <div style={{ overflowX: 'auto' }}>
      <table>
        <thead>
          <tr>
            <th>Event</th>
            <th>Status</th>
            <th>HTTP</th>
            <th>Attempt</th>
            <th>Endpoint</th>
            <th>Fired At</th>
          </tr>
        </thead>
        <tbody>
          {events.map(ev => (
            <tr key={ev.id}>
              <td>
                <span className="chip">{ev.event_type}</span>
              </td>
              <td>
                <span className={`badge badge-${ev.status === 'delivered' ? 'approved' : 'rejected'}`}>
                  {ev.status}
                </span>
              </td>
              <td style={{ fontFamily: 'var(--mono)', fontSize: 12,
                color: ev.http_status && ev.http_status < 400 ? 'var(--green)' : 'var(--red)' }}>
                {ev.http_status || '—'}
              </td>
              <td style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--text-muted)' }}>
                {ev.attempt}
              </td>
              <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12 }}>
                {ev.endpoint_url}
              </td>
              <td style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                {new Date(ev.fired_at).toLocaleString('en-IN')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
