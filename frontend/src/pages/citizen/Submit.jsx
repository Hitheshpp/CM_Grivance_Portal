import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api';
import { Alert, PriorityBadge, useMeta } from '../../components/ui';

export default function SubmitGrievance() {
  const meta = useMeta();
  const [form, setForm] = useState({ district: '', category: '', subject: '', description: '', priority: 'Medium' });
  const [file, setFile] = useState(null);
  const [ai, setAi] = useState(null);
  const [aiState, setAiState] = useState({ busy: false, error: '' });
  const [state, setState] = useState({ busy: false, error: '' });
  const [done, setDone] = useState(null);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function analyze() {
    setAiState({ busy: true, error: '' });
    try {
      setAi(await api('/api/ai/analyze', { method: 'POST', json: {
        description: form.description, subject: form.subject, district: form.district } }));
      setAiState({ busy: false, error: '' });
    } catch (e) {
      setAiState({ busy: false, error: e.message });
    }
  }

  const applySuggestion = () => setForm({ ...form, category: ai.category, priority: ai.priority });

  async function submit(e) {
    e.preventDefault();
    setState({ busy: true, error: '' });
    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => fd.append(k, v));
    if (file) fd.append('file', file);
    try {
      setDone(await api('/api/grievances', { method: 'POST', form: fd }));
    } catch (err) {
      setState({ busy: false, error: err.message });
    }
  }

  if (done) {
    return (
      <div className="container center" style={{ maxWidth: 640 }}>
        <div className="card">
          <h1>Grievance submitted</h1>
          <p>Your reference number is</p>
          <p><span className="ref-box">{done.reference_no}</span></p>
          <p className="muted">Save this number to track your grievance. Target resolution date: {new Date(done.due_date).toLocaleDateString('en-IN')}.</p>
          <div className="btn-row" style={{ justifyContent: 'center' }}>
            <Link className="btn" to={`/grievances/${done.reference_no}`}>View grievance</Link>
            <Link className="btn secondary" to="/citizen">Go to dashboard</Link>
          </div>
        </div>
      </div>
    );
  }

  const descOk = form.description.trim().length >= 20;

  return (
    <div className="container">
      <h1>Submit a Grievance</h1>
      <div className="detail-grid" style={{ gridTemplateColumns: '1fr 380px' }}>
        <form className="card" onSubmit={submit}>
          <Alert>{state.error}</Alert>
          <div className="grid cols-2">
            <div className="field"><label htmlFor="g-district">District</label>
              <select id="g-district" required value={form.district} onChange={set('district')}>
                <option value="">Select district</option>{meta?.districts.map((d) => <option key={d}>{d}</option>)}
              </select></div>
            <div className="field"><label htmlFor="g-cat">Category</label>
              <select id="g-cat" required value={form.category} onChange={set('category')}>
                <option value="">Select category</option>{meta?.categories.map((d) => <option key={d}>{d}</option>)}
              </select></div>
          </div>
          <div className="field"><label htmlFor="g-subject">Subject</label>
            <input id="g-subject" required minLength={5} maxLength={200} value={form.subject} onChange={set('subject')} /></div>
          <div className="field"><label htmlFor="g-desc">Detailed description <span className="hint">(at least 20 characters)</span></label>
            <textarea id="g-desc" required minLength={20} maxLength={5000} value={form.description} onChange={set('description')}
              style={{ minHeight: 170 }} /></div>
          <div className="grid cols-2">
            <div className="field"><label htmlFor="g-prio">Priority <span className="hint">(you may adjust; CMO reviews)</span></label>
              <select id="g-prio" value={form.priority} onChange={set('priority')}>
                {meta?.priorities.map((p) => <option key={p}>{p}</option>)}
              </select></div>
            <div className="field"><label htmlFor="g-file">Supporting file <span className="hint">(optional – PDF/JPG/PNG/WEBP, max 5 MB)</span></label>
              <input id="g-file" type="file" accept=".pdf,.jpg,.jpeg,.png,.webp,application/pdf,image/*"
                onChange={(e) => setFile(e.target.files[0] || null)} /></div>
          </div>
          <p className="small muted">Do not include real personal data – this is a prototype.</p>
          <button className="btn large" disabled={state.busy}>{state.busy ? 'Submitting…' : 'Submit grievance'}</button>
        </form>

        <aside className="ai-box" aria-live="polite">
          <h4><span className="pill-ai">AI</span> Grievance Assistant</h4>
          <p className="small">Get a suggested category, priority, department and summary. Suggestions are advisory – you decide, and the CMO team reviews everything.</p>
          <button type="button" className="btn secondary small" onClick={analyze} disabled={!descOk || aiState.busy}>
            {aiState.busy ? 'Analysing…' : 'Analyse my description'}
          </button>
          {!descOk && <p className="hint">Write at least 20 characters first.</p>}
          <Alert>{aiState.error}</Alert>
          {ai && (
            <div style={{ marginTop: '1rem' }}>
              <p className="small">
                {ai.is_fallback
                  ? <><span className="pill-fallback">FALLBACK</span> {ai.note} Basic keyword matching – lower accuracy.</>
                  : <>Generated by <strong>{ai.provider}</strong> ({ai.model})</>}
              </p>
              <dl className="meta" style={{ gridTemplateColumns: '1fr' }}>
                <div><dt>Suggested category</dt><dd>{ai.category}</dd></div>
                <div><dt>Likely department</dt><dd>{ai.department_name || '—'}</dd></div>
                <div><dt>Suggested priority</dt><dd><PriorityBadge priority={ai.priority} /></dd></div>
                <div><dt>Summary for CMO</dt><dd style={{ fontWeight: 400 }}>{ai.summary}</dd></div>
              </dl>
              {ai.duplicates.length > 0 && (
                <Alert kind="warn">
                  <strong>Possible duplicates:</strong>
                  <ul style={{ margin: '.3rem 0 0', paddingLeft: '1.1rem' }}>
                    {ai.duplicates.map((d) => <li key={d.reference_no}>{d.reference_no} – {d.subject} ({Math.round(d.similarity * 100)}% similar)</li>)}
                  </ul>
                  <span className="small">If this is the same issue, consider tracking the existing grievance instead.</span>
                </Alert>
              )}
              <button type="button" className="btn small" onClick={applySuggestion}>Use suggested category &amp; priority</button>
              <p className="hint" style={{ marginTop: '.6rem' }}>{ai.disclaimer}</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
