import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, openAttachment } from '../api';
import { useAuth } from '../auth';
import { Alert, PriorityBadge, Spinner, StatusBadge, Timeline, formatDateTime, useMeta } from '../components/ui';

export default function GrievanceDetail() {
  const { ref } = useParams();
  const { user } = useAuth();
  const [g, setG] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = useCallback(() => api(`/api/grievances/${ref}`).then(setG).catch((e) => setError(e.message)), [ref]);
  useEffect(() => { load(); }, [load]);

  /** Runs an action; on success replaces the grievance with the returned detail. */
  const act = useCallback(async (fn, okMsg) => {
    setError(''); setNotice('');
    try {
      const res = await fn();
      if (res?.reference_no) setG(res); else await load();
      setNotice(okMsg || res?.message || 'Saved');
      return true;
    } catch (e) {
      setError(e.message);
      return false;
    }
  }, [load]);

  if (error && !g) return <div className="container"><Alert>{error}</Alert><Link to={-1}>← Back</Link></div>;
  if (!g) return <div className="container"><Spinner /></div>;

  const staff = user.role !== 'citizen';
  return (
    <div className="container">
      <p><Link to={`/${user.role}`}>← Back to dashboard</Link></p>
      <Alert>{error}</Alert>
      <Alert kind="success">{notice}</Alert>
      <div className="detail-grid">
        <div>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '.5rem' }}>
              <h1 style={{ fontSize: '1.4rem', margin: 0 }}>{g.reference_no}</h1>
              <div className="btn-row">
                <StatusBadge status={g.status} /><PriorityBadge priority={g.priority} />
                {g.overdue && <span className="badge overdue">Overdue</span>}
                {g.escalated && <span className="badge high">Escalated</span>}
              </div>
            </div>
            <h2 style={{ marginTop: '.6rem' }}>{g.subject}</h2>
            <dl className="meta">
              <div><dt>District</dt><dd>{g.district}</dd></div>
              <div><dt>Category</dt><dd>{g.category}</dd></div>
              <div><dt>Department</dt><dd>{g.department || 'Awaiting assignment'}</dd></div>
              {staff && <div><dt>Assigned officer</dt><dd>{g.assigned_officer || '—'}</dd></div>}
              <div><dt>Submitted</dt><dd>{formatDateTime(g.created_at)}</dd></div>
              <div><dt>Target date</dt><dd>{formatDateTime(g.due_date)}</dd></div>
              {g.citizen && <div><dt>Citizen</dt><dd>{g.citizen.name}<br /><span className="small muted">{g.citizen.mobile}</span></dd></div>}
              {g.citizen_name && <div><dt>Citizen</dt><dd>{g.citizen_name}</dd></div>}
            </dl>
            <h3>Description</h3>
            <p style={{ whiteSpace: 'pre-wrap' }}>{g.description}</p>
            {g.attachments.length > 0 && (
              <>
                <h3>Attachments</h3>
                <div className="btn-row">
                  {g.attachments.map((a) => (
                    <button key={a.id} className="btn secondary small" onClick={() => act(() => openAttachment(g.reference_no, a), 'Opened attachment')}>
                      📎 {a.filename} <span className="muted">({Math.ceil(a.size / 1024)} KB{a.kind === 'action_report' ? ', action report' : ''})</span>
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          {g.action_taken_report && (
            <div className="card">
              <h3>Action-taken report {g.report_status && <span className="badge neutral">{g.report_status}</span>}</h3>
              <p style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>{g.action_taken_report}</p>
            </div>
          )}

          {g.ai && <AiCard ai={g.ai} />}

          {g.feedback.length > 0 && (
            <div className="card"><h3>Citizen feedback</h3>
              {g.feedback.map((f) => <p key={f.id} style={{ margin: 0 }}>{'★'.repeat(f.rating)}{'☆'.repeat(5 - f.rating)} {f.comment}</p>)}
            </div>
          )}

          <div className="card">
            <h3>Status history &amp; updates</h3>
            <Timeline items={g.history} showActorName={staff} />
          </div>
        </div>

        <div>
          {user.role === 'citizen' && <CitizenPanel g={g} act={act} />}
          {user.role === 'officer' && <OfficerPanel g={g} act={act} />}
          {user.role === 'cmo' && <CmoPanel g={g} act={act} />}
        </div>
      </div>
    </div>
  );
}

function AiCard({ ai }) {
  return (
    <div className="ai-box" style={{ marginBottom: '1rem' }}>
      <h4><span className={ai.is_fallback ? 'pill-fallback' : 'pill-ai'}>{ai.is_fallback ? 'FALLBACK' : 'AI'}</span> AI triage suggestion
        {ai.reviewed_by_human && <span className="badge resolved">Reviewed by CMO</span>}</h4>
      <dl className="meta">
        <div><dt>Suggested department</dt><dd>{ai.department || '—'}</dd></div>
        <div><dt>Suggested category</dt><dd>{ai.category}</dd></div>
        <div><dt>Suggested priority</dt><dd>{ai.priority}</dd></div>
        <div><dt>Source</dt><dd>{ai.provider}</dd></div>
      </dl>
      <p><strong>Summary:</strong> {ai.summary}</p>
      {ai.duplicates.length > 0 && (
        <Alert kind="warn"><strong>Possible duplicates (human review needed):</strong>{' '}
          {ai.duplicates.map((d) => `${d.reference_no} (${Math.round(d.similarity * 100)}%)`).join(', ')}</Alert>
      )}
      <p className="hint" style={{ margin: 0 }}>{ai.notice}</p>
    </div>
  );
}

/* ----------------------------------------------------------------- citizen */
function CitizenPanel({ g, act }) {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [reason, setReason] = useState('');
  return (
    <>
      {g.status === 'Resolved' && g.can_give_feedback && (
        <form className="card" onSubmit={(e) => { e.preventDefault(); act(() => api(`/api/grievances/${g.reference_no}/feedback`, { method: 'POST', json: { rating, comment: comment || null } })); }}>
          <h3>Rate the resolution</h3>
          <div role="radiogroup" aria-label="Rating">
            {[1, 2, 3, 4, 5].map((n) => (
              <button type="button" key={n} className={`star ${n <= rating ? 'on' : ''}`} role="radio" aria-checked={rating === n}
                aria-label={`${n} star${n > 1 ? 's' : ''}`} onClick={() => setRating(n)}>★</button>
            ))}
          </div>
          <div className="field"><label htmlFor="fb">Comments (optional)</label>
            <textarea id="fb" style={{ minHeight: 80 }} value={comment} onChange={(e) => setComment(e.target.value)} maxLength={1000} /></div>
          <button className="btn" disabled={!rating}>Submit feedback</button>
        </form>
      )}
      {g.status === 'Resolved' && (
        <form className="card" onSubmit={(e) => { e.preventDefault(); act(() => api(`/api/grievances/${g.reference_no}/status`, { method: 'PATCH', json: { status: 'Reopened', remarks: reason } }), 'Grievance reopened'); }}>
          <h3>Not satisfied?</h3>
          <div className="field"><label htmlFor="reopen">Reason for reopening</label>
            <textarea id="reopen" style={{ minHeight: 80 }} required minLength={5} value={reason} onChange={(e) => setReason(e.target.value)} /></div>
          <button className="btn danger">Reopen grievance</button>
        </form>
      )}
      {g.status !== 'Resolved' && (
        <div className="card"><h3>What happens next?</h3>
          <p className="small muted" style={{ marginBottom: 0 }}>You will see CMO and officer updates in the history. Once the CMO accepts the department's report, the grievance is marked Resolved and you can give feedback or reopen it.</p></div>
      )}
    </>
  );
}

/* ----------------------------------------------------------------- officer */
function OfficerPanel({ g, act }) {
  const [remark, setRemark] = useState('');
  const [vis, setVis] = useState('public');
  const [report, setReport] = useState('');
  const [file, setFile] = useState(null);

  const setStatus = (status, remarks) => act(() => api(`/api/grievances/${g.reference_no}/status`, { method: 'PATCH', json: { status, remarks } }), `Status set to ${status}`);
  const canStart = g.status === 'Under Review' || g.status === 'Reopened';
  const canReport = g.status === 'In Progress' && g.report_status !== 'Pending CMO Review';

  return (
    <>
      <div className="card"><h3>Update status</h3>
        {canStart ? <button className="btn" onClick={() => setStatus('In Progress', 'Investigation started')}>Mark In Progress</button>
          : <p className="muted small" style={{ margin: 0 }}>Current status: <StatusBadge status={g.status} />.
            {g.status === 'In Progress' ? ' Submit the action-taken report when work is complete.' : ' No status change available.'}</p>}
        {g.report_status === 'Rejected' && <Alert kind="warn">The CMO returned your last report. See the remarks in the history and resubmit.</Alert>}
      </div>

      <form className="card" onSubmit={async (e) => { e.preventDefault(); if (await act(() => api(`/api/grievances/${g.reference_no}/remarks`, { method: 'POST', json: { remarks: remark, visibility: vis } }), 'Remark added')) setRemark(''); }}>
        <h3>Add investigation remark</h3>
        <div className="field"><label htmlFor="o-rem">Remark</label>
          <textarea id="o-rem" style={{ minHeight: 80 }} required minLength={2} value={remark} onChange={(e) => setRemark(e.target.value)} /></div>
        <div className="field"><label htmlFor="o-vis">Visible to</label>
          <select id="o-vis" value={vis} onChange={(e) => setVis(e.target.value)}>
            <option value="public">Citizen, CMO and department</option><option value="department">CMO and department only</option></select></div>
        <button className="btn secondary">Add remark</button>
      </form>

      {canReport && (
        <form className="card" onSubmit={async (e) => {
          e.preventDefault();
          const fd = new FormData(); fd.append('report_text', report); if (file) fd.append('file', file);
          if (await act(() => api(`/api/officer/grievances/${g.reference_no}/report`, { method: 'POST', form: fd }), 'Report submitted to the CMO')) { setReport(''); setFile(null); }
        }}>
          <h3>Action-taken report</h3>
          <div className="field"><label htmlFor="o-rep">Report <span className="hint">(min 20 characters)</span></label>
            <textarea id="o-rep" required minLength={20} maxLength={8000} value={report} onChange={(e) => setReport(e.target.value)} /></div>
          <div className="field"><label htmlFor="o-file">Supporting document (optional)</label>
            <input id="o-file" type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" onChange={(e) => setFile(e.target.files[0] || null)} /></div>
          <button className="btn accent">Submit to CMO for review</button>
        </form>
      )}
      {g.report_status === 'Pending CMO Review' && <Alert kind="info">Your report is awaiting CMO review.</Alert>}
    </>
  );
}

/* --------------------------------------------------------------------- CMO */
const CMO_STATUS_ACTIONS = {
  Submitted: [['Under Review', 'Start review']],
  'Under Review': [['In Progress', 'Mark In Progress']],
  'In Progress': [['Under Review', 'Move back to Under Review']],
  Reopened: [['Under Review', 'Move to Under Review'], ['In Progress', 'Mark In Progress']],
};

function CmoPanel({ g, act }) {
  const meta = useMeta();
  const [depts, setDepts] = useState([]);
  const [officers, setOfficers] = useState([]);
  const [assign, setAssign] = useState({ department_id: '', officer_id: '', note: '' });
  const [triage, setTriage] = useState({ category: g.category, priority: g.priority, remarks: '' });
  const [esc, setEsc] = useState('');
  const [remark, setRemark] = useState({ text: '', vis: 'internal' });
  const [review, setReview] = useState('');

  useEffect(() => { api('/api/public/departments').then(setDepts).catch(() => {}); }, []);
  // Pre-select the likely department (AI suggestion, else the one matching the category). CMO can change it.
  const suggestedDept = depts.find((d) => d.name === g.ai?.department) || depts.find((d) => d.category === g.category);
  useEffect(() => {
    if (suggestedDept && !g.department) setAssign((a) => (a.department_id ? a : { ...a, department_id: String(suggestedDept.id) }));
  }, [suggestedDept, g.department]);
  useEffect(() => {
    setTriage({ category: g.category, priority: g.priority, remarks: '' });
  }, [g.category, g.priority]);
  useEffect(() => {
    if (!assign.department_id) { setOfficers([]); return; }
    api(`/api/cmo/officers?department_id=${assign.department_id}`).then(setOfficers).catch(() => setOfficers([]));
  }, [assign.department_id]);

  const base = `/api/cmo/grievances/${g.reference_no}`;
  const resolved = g.status === 'Resolved';

  return (
    <>
      {g.report_status === 'Pending CMO Review' && (
        <div className="card" style={{ borderColor: 'var(--accent)' }}>
          <h3>Review action-taken report</h3>
          <p className="small muted">The department has submitted its report (shown on the left). Accept to resolve, or return it with remarks.</p>
          <div className="field"><label htmlFor="rv">Remarks <span className="hint">(required when returning)</span></label>
            <textarea id="rv" style={{ minHeight: 70 }} value={review} onChange={(e) => setReview(e.target.value)} /></div>
          <div className="btn-row">
            <button className="btn" onClick={() => act(() => api(`${base}/review-report`, { method: 'POST', json: { decision: 'accept', remarks: review || null } }), 'Report accepted – grievance resolved')}>Accept &amp; resolve</button>
            <button className="btn danger" onClick={() => act(() => api(`${base}/review-report`, { method: 'POST', json: { decision: 'reject', remarks: review } }), 'Report returned to department')}>Return</button>
          </div>
        </div>
      )}

      <div className="card"><h3>Review AI suggestion / triage</h3>
        <div className="field"><label htmlFor="t-cat">Category</label>
          <select id="t-cat" value={triage.category} onChange={(e) => setTriage({ ...triage, category: e.target.value })}>
            {meta?.categories.map((c) => <option key={c}>{c}</option>)}</select></div>
        <div className="field"><label htmlFor="t-pr">Priority</label>
          <select id="t-pr" value={triage.priority} onChange={(e) => setTriage({ ...triage, priority: e.target.value })}>
            {meta?.priorities.map((c) => <option key={c}>{c}</option>)}</select></div>
        <div className="field"><label htmlFor="t-rm">Note (optional)</label>
          <input id="t-rm" value={triage.remarks} onChange={(e) => setTriage({ ...triage, remarks: e.target.value })} /></div>
        <button className="btn secondary" onClick={() => act(() => api(`${base}/triage`, { method: 'PATCH', json: { category: triage.category, priority: triage.priority, remarks: triage.remarks || null } }), 'Triage recorded')}>
          Confirm / save triage</button>
      </div>

      {!resolved && (
        <form className="card" onSubmit={(e) => { e.preventDefault(); act(() => api(`${base}/assign`, { method: 'POST', json: { department_id: Number(assign.department_id), officer_id: assign.officer_id ? Number(assign.officer_id) : null, note: assign.note || null } }), 'Grievance forwarded'); }}>
          <h3>{g.department ? 'Reassign' : 'Forward to department'}</h3>
          {suggestedDept && !g.department && <p className="small muted">Pre-selected from the AI/category suggestion: {suggestedDept.name}. Change it if needed.</p>}
          <div className="field"><label htmlFor="a-d">Department</label>
            <select id="a-d" required value={assign.department_id} onChange={(e) => setAssign({ ...assign, department_id: e.target.value, officer_id: '' })}>
              <option value="">Select department</option>{depts.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</select></div>
          <div className="field"><label htmlFor="a-o">Officer (optional)</label>
            <select id="a-o" value={assign.officer_id} onChange={(e) => setAssign({ ...assign, officer_id: e.target.value })}>
              <option value="">Any officer in department</option>{officers.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}</select></div>
          <div className="field"><label htmlFor="a-n">Instruction (optional)</label>
            <input id="a-n" value={assign.note} onChange={(e) => setAssign({ ...assign, note: e.target.value })} /></div>
          <button className="btn">Forward</button>
        </form>
      )}

      {(CMO_STATUS_ACTIONS[g.status] || []).length > 0 && (
        <div className="card"><h3>Status</h3>
          <div className="btn-row">
            {CMO_STATUS_ACTIONS[g.status].map(([to, label]) => (
              <button key={to + label} className="btn secondary small" onClick={() => act(() => api(`/api/grievances/${g.reference_no}/status`, { method: 'PATCH', json: { status: to } }), `Status set to ${to}`)}>{label}</button>
            ))}
          </div>
        </div>
      )}

      <form className="card" onSubmit={async (e) => { e.preventDefault(); if (await act(() => api(`/api/grievances/${g.reference_no}/remarks`, { method: 'POST', json: { remarks: remark.text, visibility: remark.vis } }), 'Remark added')) setRemark({ ...remark, text: '' }); }}>
        <h3>Add remark</h3>
        <div className="field"><label htmlFor="m-t">Remark</label>
          <textarea id="m-t" style={{ minHeight: 70 }} required minLength={2} value={remark.text} onChange={(e) => setRemark({ ...remark, text: e.target.value })} /></div>
        <div className="field"><label htmlFor="m-v">Visible to</label>
          <select id="m-v" value={remark.vis} onChange={(e) => setRemark({ ...remark, vis: e.target.value })}>
            <option value="internal">CMO only (internal)</option><option value="department">CMO and department</option><option value="public">Everyone incl. citizen</option></select></div>
        <button className="btn secondary">Add remark</button>
      </form>

      {!resolved && !g.escalated && (
        <form className="card" onSubmit={(e) => { e.preventDefault(); act(() => api(`${base}/escalate`, { method: 'POST', json: { reason: esc } }), 'Escalated'); }}>
          <h3>Escalate</h3>
          <p className="small muted">Marks the grievance High priority and flags it to the department.{g.overdue ? ' This grievance is overdue.' : ''}</p>
          <div className="field"><label htmlFor="e-r">Reason</label>
            <input id="e-r" required minLength={5} value={esc} onChange={(e) => setEsc(e.target.value)} /></div>
          <button className="btn danger">Escalate</button>
        </form>
      )}
    </>
  );
}
