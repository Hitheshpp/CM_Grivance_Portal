import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../auth';
import { Alert, Pagination, PriorityBadge, Spinner, StatusBadge, formatDate, useFetch, useMeta } from '../../components/ui';

export default function CitizenDashboard() {
  const { user } = useAuth();
  const meta = useMeta();
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const summary = useFetch('/api/grievances/dashboard-summary');
  const list = useFetch(`/api/grievances?page=${page}&page_size=8${status ? `&status=${encodeURIComponent(status)}` : ''}`);
  const s = summary.data;

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '.6rem' }}>
        <h1 style={{ margin: 0 }}>Welcome, {user.name}</h1>
        <Link className="btn accent" to="/citizen/submit">+ Submit new grievance</Link>
      </div>

      <div className="grid cols-4" style={{ margin: '1.2rem 0' }}>
        <div className="card stat"><div className="num">{s?.total ?? '–'}</div><div className="lbl">Submitted</div></div>
        <div className="card stat warn"><div className="num">{s?.pending ?? '–'}</div><div className="lbl">Pending</div></div>
        <div className="card stat ok"><div className="num">{s?.resolved ?? '–'}</div><div className="lbl">Resolved</div></div>
        <div className="card stat danger"><div className="num">{s?.overdue ?? '–'}</div><div className="lbl">Overdue</div></div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '.6rem', alignItems: 'end' }}>
          <h2 style={{ margin: 0 }}>My grievances</h2>
          <div style={{ minWidth: 200 }}>
            <label htmlFor="f-status" className="sr-only">Filter by status</label>
            <select id="f-status" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
              <option value="">All statuses</option>
              {meta?.statuses.map((x) => <option key={x}>{x}</option>)}
            </select>
          </div>
        </div>
        {list.loading && <Spinner />}
        <Alert>{list.error}</Alert>
        {list.data && (list.data.items.length === 0 ? (
          <p className="muted" style={{ marginTop: '1rem' }}>No grievances yet. <Link to="/citizen/submit">Submit your first grievance.</Link></p>
        ) : (
          <div className="table-wrap" style={{ marginTop: '1rem' }}>
            <table className="data">
              <thead><tr><th>Reference</th><th>Subject</th><th>Category</th><th>Department</th><th>Priority</th><th>Status</th><th>Submitted</th></tr></thead>
              <tbody>
                {list.data.items.map((g) => (
                  <tr key={g.reference_no}>
                    <td><Link to={`/grievances/${g.reference_no}`}>{g.reference_no}</Link></td>
                    <td>{g.subject}</td><td>{g.category}</td><td>{g.department || '—'}</td>
                    <td><PriorityBadge priority={g.priority} /></td>
                    <td><StatusBadge status={g.status} /> {g.overdue && <span className="badge overdue">Overdue</span>}</td>
                    <td>{formatDate(g.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
        {list.data && <Pagination page={page} pageSize={8} total={list.data.total} onChange={setPage} />}
      </div>
    </div>
  );
}
