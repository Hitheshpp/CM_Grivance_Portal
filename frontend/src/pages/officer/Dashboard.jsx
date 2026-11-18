import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../auth';
import { Alert, Pagination, PriorityBadge, Spinner, StatusBadge, formatDate, useFetch, useMeta } from '../../components/ui';

export default function OfficerDashboard() {
  const { user } = useAuth();
  const meta = useMeta();
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const summary = useFetch('/api/grievances/dashboard-summary').data;
  const list = useFetch(`/api/grievances?page=${page}&page_size=10${status ? `&status=${encodeURIComponent(status)}` : ''}`);

  return (
    <div className="container">
      <h1>Officer Dashboard</h1>
      <p className="muted">{user.name} · {user.department}</p>
      <div className="grid cols-4" style={{ margin: '1rem 0' }}>
        <div className="card stat"><div className="num">{summary?.total ?? '–'}</div><div className="lbl">Forwarded to my department</div></div>
        <div className="card stat warn"><div className="num">{summary?.pending ?? '–'}</div><div className="lbl">Pending</div></div>
        <div className="card stat ok"><div className="num">{summary?.resolved ?? '–'}</div><div className="lbl">Resolved</div></div>
        <div className="card stat danger"><div className="num">{summary?.overdue ?? '–'}</div><div className="lbl">Overdue</div></div>
      </div>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '.6rem', alignItems: 'end' }}>
          <h2 style={{ margin: 0 }}>Assigned grievances</h2>
          <div style={{ minWidth: 200 }}>
            <label htmlFor="o-status" className="sr-only">Filter by status</label>
            <select id="o-status" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
              <option value="">All statuses</option>{meta?.statuses.map((x) => <option key={x}>{x}</option>)}
            </select>
          </div>
        </div>
        {list.loading && <Spinner />}<Alert>{list.error}</Alert>
        {list.data && (list.data.items.length === 0 ? <p className="muted" style={{ marginTop: '1rem' }}>Nothing assigned.</p> : (
          <div className="table-wrap" style={{ marginTop: '1rem' }}>
            <table className="data">
              <thead><tr><th>Reference</th><th>Subject</th><th>District</th><th>Priority</th><th>Status</th><th>Target</th></tr></thead>
              <tbody>
                {list.data.items.map((g) => (
                  <tr key={g.reference_no}>
                    <td><Link to={`/grievances/${g.reference_no}`}>{g.reference_no}</Link></td>
                    <td>{g.subject}</td><td>{g.district}</td><td><PriorityBadge priority={g.priority} /></td>
                    <td><StatusBadge status={g.status} />{g.report_status === 'Rejected' && <> <span className="badge high">Report returned</span></>}</td>
                    <td>{formatDate(g.due_date)} {g.overdue && <span className="badge overdue">Overdue</span>}{g.escalated && <> <span className="badge high">Escalated</span></>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
        {list.data && <Pagination page={page} pageSize={10} total={list.data.total} onChange={setPage} />}
      </div>
    </div>
  );
}
