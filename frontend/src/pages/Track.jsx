import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api';
import { Alert, PriorityBadge, StatusBadge, Timeline, formatDateTime } from '../components/ui';

export default function Track() {
  const { ref: refParam } = useParams();
  const navigate = useNavigate();
  const [ref, setRef] = useState(refParam || '');
  const [result, setResult] = useState(null);
  const [state, setState] = useState({ busy: false, error: '' });

  async function lookup(value) {
    setState({ busy: true, error: '' });
    setResult(null);
    try {
      setResult(await api(`/api/public/track/${encodeURIComponent(value.trim())}`));
      setState({ busy: false, error: '' });
    } catch (e) {
      setState({ busy: false, error: e.message });
    }
  }

  useEffect(() => { if (refParam) lookup(refParam); /* eslint-disable-next-line */ }, [refParam]);

  function submit(e) {
    e.preventDefault();
    if (ref.trim()) navigate(`/track/${encodeURIComponent(ref.trim())}`);
  }

  return (
    <div className="container" style={{ maxWidth: 820 }}>
      <h1>Track Grievance</h1>
      <form className="card" onSubmit={submit}>
        <label htmlFor="ref">Reference number</label>
        <div style={{ display: 'flex', gap: '.6rem', flexWrap: 'wrap' }}>
          <input id="ref" style={{ flex: 1, minWidth: 220 }} placeholder="e.g. KGR-2026-000012" value={ref}
            onChange={(e) => setRef(e.target.value)} />
          <button className="btn" disabled={state.busy}>{state.busy ? 'Searching…' : 'Track'}</button>
        </div>
        <p className="hint" style={{ margin: '.5rem 0 0' }}>Public tracking shows status and public updates only. Log in to see full details of your own grievances.</p>
      </form>
      <div style={{ marginTop: '1rem' }}><Alert>{state.error}</Alert></div>
      {result && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '.5rem' }}>
            <h2 style={{ margin: 0 }}>{result.reference_no}</h2>
            <div className="btn-row"><StatusBadge status={result.status} /><PriorityBadge priority={result.priority} />
              {result.overdue && <span className="badge overdue">Overdue</span>}</div>
          </div>
          <p style={{ marginTop: '.6rem' }}><strong>{result.subject}</strong></p>
          <dl className="meta">
            <div><dt>District</dt><dd>{result.district}</dd></div>
            <div><dt>Category</dt><dd>{result.category}</dd></div>
            <div><dt>Assigned department</dt><dd>{result.department || 'Awaiting assignment'}</dd></div>
            <div><dt>Submitted</dt><dd>{formatDateTime(result.created_at)}</dd></div>
            <div><dt>Last updated</dt><dd>{formatDateTime(result.updated_at)}</dd></div>
          </dl>
          <h3>Status history</h3>
          <Timeline items={result.history} />
        </div>
      )}
    </div>
  );
}
