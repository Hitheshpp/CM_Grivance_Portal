import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api';
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Alert, Pagination, PriorityBadge, Spinner, StatusBadge, formatDate, formatDateTime, useFetch, useMeta } from '../../components/ui';

const STATUS_COLORS = { Submitted: '#78909c', 'Under Review': '#c98a00', 'In Progress': '#1b5aa8', Resolved: '#1b7a3d', Reopened: '#b3261e' };
const EMPTY = { status: '', district: '', category: '', priority: '', overdue: '', q: '' };

export default function CmoDashboard() {
  const [tab, setTab] = useState('overview');
  const [filters, setFilters] = useState(EMPTY);
  const [page, setPage] = useState(1);
  const stats = useFetch('/api/cmo/stats');

  const quick = (patch) => { setFilters({ ...EMPTY, ...patch }); setPage(1); setTab('grievances'); };

  return (
    <div className="container">
      <h1>CMO Dashboard</h1>
      <div className="tabs" role="tablist">
        {[['overview', 'Overview & statistics'], ['grievances', 'All grievances'], ['officers', 'Manage officers'], ['enquiries', 'Contact enquiries']].map(([k, l]) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}>{l}</button>
        ))}
      </div>
      {tab === 'overview' && <Overview stats={stats} quick={quick} />}
      {tab === 'grievances' && <GrievanceList filters={filters} setFilters={setFilters} page={page} setPage={setPage} />}
      {tab === 'officers' && <Officers />}
      {tab === 'enquiries' && <Enquiries />}
    </div>
  );
}

const EMPTY_OFFICER = { name: '', email: '', mobile: '', password: '', department_id: '' };

function Officers() {
  const [reload, setReload] = useState(0);
  const depts = useFetch('/api/public/departments').data || [];
  const { data: officers, loading, error } = useFetch('/api/cmo/officers?include_inactive=true', [reload]);
  const [form, setForm] = useState(EMPTY_OFFICER);
  const [msg, setMsg] = useState({ kind: 'success', text: '' });
  const [busy, setBusy] = useState(false);
  const [resetting, setResetting] = useState(null); // { id, password }
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const run = async (fn, okText) => {
    setBusy(true); setMsg({ kind: 'success', text: '' });
    try {
      const r = await fn();
      setMsg({ kind: 'success', text: okText || r?.message || 'Done' });
      setReload((n) => n + 1);
      return true;
    } catch (e) {
      setMsg({ kind: 'error', text: e.message });
      return false;
    } finally { setBusy(false); }
  };

  const create = async (e) => {
    e.preventDefault();
    const ok = await run(() => api('/api/cmo/officers', { method: 'POST', json: { ...form, department_id: Number(form.department_id) } }),
      `Officer account created for ${form.name}. Share the temporary password securely.`);
    if (ok) setForm(EMPTY_OFFICER);
  };

  return (
    <div className="detail-grid" style={{ gridTemplateColumns: '1fr 380px' }}>
      <div className="card">
        <h3>Department officers</h3>
        <Alert kind={msg.kind}>{msg.text}</Alert>
        {loading && <Spinner />}<Alert>{error}</Alert>
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>Name</th><th>Email</th><th>Department</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
              {(officers || []).map((o) => (
                <tr key={o.id}>
                  <td>{o.name}</td><td>{o.email}</td><td>{o.department}</td>
                  <td><span className={`badge ${o.is_active ? 'resolved' : 'neutral'}`}>{o.is_active ? 'Active' : 'Deactivated'}</span></td>
                  <td>
                    {resetting?.id === o.id ? (
                      <form className="btn-row" onSubmit={async (e) => { e.preventDefault(); if (await run(() => api(`/api/cmo/officers/${o.id}/reset-password`, { method: 'POST', json: { password: resetting.password } }))) setResetting(null); }}>
                        <label className="sr-only" htmlFor={`rp-${o.id}`}>New password</label>
                        <input id={`rp-${o.id}`} type="text" autoComplete="off" placeholder="New password" minLength={8} required style={{ width: 150 }}
                          value={resetting.password} onChange={(e) => setResetting({ id: o.id, password: e.target.value })} />
                        <button className="btn small" disabled={busy}>Save</button>
                        <button type="button" className="btn secondary small" onClick={() => setResetting(null)}>Cancel</button>
                      </form>
                    ) : (
                      <div className="btn-row">
                        <button className="btn secondary small" disabled={busy} onClick={() => setResetting({ id: o.id, password: '' })}>Reset password</button>
                        <button className={`btn small ${o.is_active ? 'danger' : ''}`} disabled={busy}
                          onClick={() => run(() => api(`/api/cmo/officers/${o.id}/active`, { method: 'PATCH', json: { is_active: !o.is_active } }), o.is_active ? `${o.name} deactivated` : `${o.name} reactivated`)}>
                          {o.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="hint">Deactivating blocks login immediately; the officer's past remarks and history are kept.</p>
      </div>

      <form className="card" onSubmit={create}>
        <h3>Create officer account</h3>
        <div className="field"><label htmlFor="n-name">Full name</label>
          <input id="n-name" required minLength={2} maxLength={120} value={form.name} onChange={set('name')} /></div>
        <div className="field"><label htmlFor="n-email">Email (login id)</label>
          <input id="n-email" type="email" required value={form.email} onChange={set('email')} /></div>
        <div className="field"><label htmlFor="n-mobile">Mobile <span className="hint">(10 digits)</span></label>
          <input id="n-mobile" inputMode="numeric" required pattern="(\+91)?[6-9][0-9]{9}" value={form.mobile} onChange={set('mobile')} /></div>
        <div className="field"><label htmlFor="n-dept">Department</label>
          <select id="n-dept" required value={form.department_id} onChange={set('department_id')}>
            <option value="">Select department</option>{depts.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</select></div>
        <div className="field"><label htmlFor="n-pass">Temporary password <span className="hint">(min 8, letters + digits)</span></label>
          <input id="n-pass" type="text" autoComplete="off" required minLength={8} maxLength={64} value={form.password} onChange={set('password')} /></div>
        <button className="btn" disabled={busy}>{busy ? 'Saving…' : 'Create officer'}</button>
        <p className="hint" style={{ marginTop: '.6rem' }}>Share the temporary password through a secure channel and ask the officer to keep it private.</p>
      </form>
    </div>
  );
}

function Overview({ stats, quick }) {
  const { data: s, loading, error } = stats;
  if (loading) return <Spinner />;
  if (error) return <Alert>{error}</Alert>;
  const card = (label, value, cls, onClick) => (
    <button className={`stat clickable ${cls || ''}`} onClick={onClick}><div className="num">{value}</div><div className="lbl">{label}</div></button>
  );
  return (
    <>
      <div className="grid cols-6">
        {card('Total', s.total, '', () => quick({}))}
        {card('Pending', s.pending, 'warn', () => quick({}))}
        {card('Resolved', s.resolved, 'ok', () => quick({ status: 'Resolved' }))}
        {card('Overdue', s.overdue, 'danger', () => quick({ overdue: 'true' }))}
        {card('Escalated', s.escalated, 'danger', () => quick({}))}
        {card('Reports to review', s.reports_pending_review, 'warn', () => quick({}))}
      </div>
      <p className="small muted" style={{ marginTop: '.5rem' }}>
        {s.unassigned} grievance(s) not yet forwarded to a department · Average citizen rating: {s.avg_feedback_rating ?? 'n/a'} / 5
      </p>

      <div className="grid cols-2" style={{ marginTop: '1rem' }}>
        <div className="card"><h3>District-wise grievances</h3>
          <div className="chart-box" style={{ height: 340 }}>
            <ResponsiveContainer><BarChart data={s.by_district} layout="vertical" margin={{ left: 40 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} /><XAxis type="number" allowDecimals={false} />
              <YAxis type="category" dataKey="label" width={120} tick={{ fontSize: 12 }} /><Tooltip /><Legend />
              <Bar dataKey="total" name="Total" fill="#0b5d4b" /><Bar dataKey="resolved" name="Resolved" fill="#8fc9b6" />
            </BarChart></ResponsiveContainer>
          </div></div>
        <div className="card"><h3>Status distribution</h3>
          <div className="chart-box" style={{ height: 340 }}>
            <ResponsiveContainer><PieChart>
              <Pie data={s.by_status} dataKey="count" nameKey="label" outerRadius={110} label={({ label, count }) => `${label} (${count})`}>
                {s.by_status.map((e) => <Cell key={e.label} fill={STATUS_COLORS[e.label] || '#999'} />)}
              </Pie><Tooltip /></PieChart></ResponsiveContainer>
          </div></div>
      </div>

      <div className="card" style={{ marginTop: '1rem' }}>
        <h3>Department-wise statistics</h3>
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>Department</th><th>Total</th><th>Resolved</th><th>Pending</th><th>Overdue</th><th>Resolution</th></tr></thead>
            <tbody>
              {s.by_department.map((d) => (
                <tr key={d.label}><td>{d.label}</td><td>{d.total}</td><td>{d.resolved}</td><td>{d.total - d.resolved}</td>
                  <td>{d.overdue > 0 ? <span className="badge overdue">{d.overdue}</span> : 0}</td>
                  <td>{d.total ? `${Math.round((d.resolved * 100) / d.total)}%` : '–'}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid cols-2" style={{ marginTop: '1rem' }}>
        <div className="card"><h3>By category</h3>
          <div className="chart-box"><ResponsiveContainer><BarChart data={s.by_category} margin={{ bottom: 50 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="label" interval={0} angle={-30} textAnchor="end" tick={{ fontSize: 11 }} />
            <YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="count" name="Grievances" fill="#b8860b" /></BarChart></ResponsiveContainer></div></div>
        <div className="card"><h3>Department-wise: resolved vs overdue</h3>
          <div className="chart-box"><ResponsiveContainer><BarChart data={s.by_department} margin={{ bottom: 50 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="label" interval={0} angle={-30} textAnchor="end" tick={{ fontSize: 11 }} />
            <YAxis allowDecimals={false} /><Tooltip /><Legend verticalAlign="top" />
            <Bar dataKey="resolved" name="Resolved" fill="#1b7a3d" /><Bar dataKey="overdue" name="Overdue" fill="#b3261e" /></BarChart></ResponsiveContainer></div></div>
      </div>
    </>
  );
}

function GrievanceList({ filters, setFilters, page, setPage }) {
  const meta = useMeta();
  const qs = new URLSearchParams({ page, page_size: 10 });
  Object.entries(filters).forEach(([k, v]) => v && qs.set(k, v));
  const { data, loading, error } = useFetch(`/api/grievances?${qs}`);
  const set = (k) => (e) => { setFilters({ ...filters, [k]: e.target.value }); setPage(1); };
  const sel = (k, label, opts) => (
    <div className="field"><label htmlFor={`f-${k}`}>{label}</label>
      <select id={`f-${k}`} value={filters[k]} onChange={set(k)}><option value="">All</option>{opts?.map((o) => <option key={o}>{o}</option>)}</select></div>
  );
  return (
    <div className="card">
      <div className="filters">
        {sel('district', 'District', meta?.districts)}{sel('category', 'Category', meta?.categories)}
        {sel('priority', 'Priority', meta?.priorities)}{sel('status', 'Status', meta?.statuses)}
        <div className="field"><label htmlFor="f-od">Overdue</label>
          <select id="f-od" value={filters.overdue} onChange={set('overdue')}><option value="">All</option><option value="true">Overdue only</option><option value="false">Not overdue</option></select></div>
        <div className="field"><label htmlFor="f-q">Search</label><input id="f-q" placeholder="Reference or subject" value={filters.q} onChange={set('q')} /></div>
        <button className="btn secondary small" onClick={() => { setFilters(EMPTY); setPage(1); }}>Clear filters</button>
      </div>
      {loading && <Spinner />}<Alert>{error}</Alert>
      {data && (data.items.length === 0 ? <p className="muted">No grievances match these filters.</p> : (
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>Reference</th><th>Subject</th><th>District</th><th>Category</th><th>Priority</th><th>Status</th><th>Department</th><th>Target</th></tr></thead>
            <tbody>
              {data.items.map((g) => (
                <tr key={g.reference_no}>
                  <td><Link to={`/grievances/${g.reference_no}`}>{g.reference_no}</Link></td>
                  <td>{g.subject}</td><td>{g.district}</td><td>{g.category}</td>
                  <td><PriorityBadge priority={g.priority} /></td>
                  <td><StatusBadge status={g.status} />{g.report_status === 'Pending CMO Review' && <> <span className="badge neutral">Report pending</span></>}</td>
                  <td>{g.department || <em className="muted">Unassigned</em>}</td>
                  <td>{formatDate(g.due_date)} {g.overdue && <span className="badge overdue">Overdue</span>}{g.escalated && <> <span className="badge high">Esc.</span></>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
      {data && <Pagination page={page} pageSize={10} total={data.total} onChange={setPage} />}
    </div>
  );
}

function Enquiries() {
  const { data, loading, error } = useFetch('/api/cmo/enquiries');
  return (
    <div className="card"><h3>Contact enquiries</h3>
      {loading && <Spinner />}<Alert>{error}</Alert>
      {data?.length === 0 && <p className="muted">No enquiries yet.</p>}
      {data?.map((e) => (
        <div key={e.id} style={{ borderBottom: '1px solid var(--line)', padding: '.7rem 0' }}>
          <strong>{e.subject}</strong> <span className="small muted">– {e.name} ({e.email}) · {formatDateTime(e.created_at)}</span>
          <p style={{ margin: '.3rem 0 0' }}>{e.message}</p>
        </div>
      ))}
    </div>
  );
}
