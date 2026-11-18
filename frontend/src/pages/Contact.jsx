import { useState } from 'react';
import { api } from '../api';
import { Alert } from '../components/ui';

export default function Contact() {
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' });
  const [state, setState] = useState({ busy: false, error: '', ok: '' });
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setState({ busy: true, error: '', ok: '' });
    try {
      const r = await api('/api/public/contact', { method: 'POST', json: form });
      setState({ busy: false, error: '', ok: r.message });
      setForm({ name: '', email: '', subject: '', message: '' });
    } catch (err) {
      setState({ busy: false, error: err.message, ok: '' });
    }
  }

  return (
    <div className="container" style={{ maxWidth: 680 }}>
      <h1>Contact Us</h1>
      <p className="muted">Questions about the portal? Send us a message. (Prototype: enquiries are stored in the demo database only.)</p>
      <form className="card" onSubmit={submit} noValidate>
        <Alert kind="success">{state.ok}</Alert>
        <Alert>{state.error}</Alert>
        <div className="field"><label htmlFor="c-name">Name</label>
          <input id="c-name" value={form.name} onChange={set('name')} required minLength={2} maxLength={120} autoComplete="name" /></div>
        <div className="field"><label htmlFor="c-email">Email</label>
          <input id="c-email" type="email" value={form.email} onChange={set('email')} required autoComplete="email" /></div>
        <div className="field"><label htmlFor="c-subject">Subject</label>
          <input id="c-subject" value={form.subject} onChange={set('subject')} required minLength={3} maxLength={200} /></div>
        <div className="field"><label htmlFor="c-message">Message <span className="hint">(10–3000 characters)</span></label>
          <textarea id="c-message" value={form.message} onChange={set('message')} required minLength={10} maxLength={3000} /></div>
        <button className="btn" disabled={state.busy}>{state.busy ? 'Sending…' : 'Send message'}</button>
      </form>
    </div>
  );
}
