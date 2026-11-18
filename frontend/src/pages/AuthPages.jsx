import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { HOME_BY_ROLE, useAuth } from '../auth';
import { Alert } from '../components/ui';

export function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: '', password: '' });
  const [state, setState] = useState({ busy: false, error: '' });

  if (user) return <Navigate to={HOME_BY_ROLE[user.role]} replace />;

  async function submit(e) {
    e.preventDefault();
    setState({ busy: true, error: '' });
    try {
      const u = await login(form.email, form.password);
      const from = location.state?.from;
      navigate(from && from !== '/login' ? from : HOME_BY_ROLE[u.role], { replace: true });
    } catch (err) {
      setState({ busy: false, error: err.message });
    }
  }

  return (
    <div className="container form-narrow">
      <h1>Login</h1>
      <form className="card" onSubmit={submit}>
        <Alert>{state.error}</Alert>
        <div className="field"><label htmlFor="l-email">Email</label>
          <input id="l-email" type="email" autoComplete="username" required value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
        <div className="field"><label htmlFor="l-pass">Password</label>
          <input id="l-pass" type="password" autoComplete="current-password" required value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })} /></div>
        <button className="btn" style={{ width: '100%' }} disabled={state.busy}>{state.busy ? 'Signing in…' : 'Login'}</button>
        <p className="center small" style={{ marginTop: '1rem', marginBottom: 0 }}>New citizen? <Link to="/register">Create an account</Link></p>
      </form>
      <DemoAccounts onPick={(email) => setForm({ email, password: 'Demo@1234' })} />
    </div>
  );
}

function DemoAccounts({ onPick }) {
  const accounts = [
    ['Citizen', 'citizen1@demo-portal.in'], ['CMO Admin', 'cmo@demo-portal.in'],
    ['Officer (PWD)', 'officer.pwd@demo-portal.in'], ['Officer (Health)', 'officer.health@demo-portal.in'],
  ];
  return (
    <div className="card" style={{ marginTop: '1rem' }}>
      <h3>Demo accounts (evaluators)</h3>
      <p className="small muted">Password for all demo accounts: <code>Demo@1234</code>. Click to fill the form.</p>
      <div className="btn-row">
        {accounts.map(([label, email]) => (
          <button key={email} type="button" className="btn secondary small" onClick={() => onPick(email)}>{label}</button>
        ))}
      </div>
    </div>
  );
}

export function Register() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', mobile: '', password: '' });
  const [state, setState] = useState({ busy: false, error: '' });
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  if (user) return <Navigate to={HOME_BY_ROLE[user.role]} replace />;

  async function submit(e) {
    e.preventDefault();
    setState({ busy: true, error: '' });
    try {
      await register(form);
      navigate('/citizen', { replace: true });
    } catch (err) {
      setState({ busy: false, error: err.message });
    }
  }

  return (
    <div className="container form-narrow">
      <h1>Citizen Registration</h1>
      <form className="card" onSubmit={submit}>
        <Alert kind="info">Use fictional details only – this is a demo.</Alert>
        <Alert>{state.error}</Alert>
        <div className="field"><label htmlFor="r-name">Full name</label>
          <input id="r-name" required minLength={2} maxLength={120} autoComplete="name" value={form.name} onChange={set('name')} /></div>
        <div className="field"><label htmlFor="r-email">Email</label>
          <input id="r-email" type="email" required autoComplete="email" value={form.email} onChange={set('email')} /></div>
        <div className="field"><label htmlFor="r-mobile">Mobile number <span className="hint">(10 digits)</span></label>
          <input id="r-mobile" inputMode="numeric" required pattern="(\+91)?[6-9][0-9]{9}" autoComplete="tel" value={form.mobile} onChange={set('mobile')} /></div>
        <div className="field"><label htmlFor="r-pass">Password <span className="hint">(min 8 characters, letters and digits)</span></label>
          <input id="r-pass" type="password" required minLength={8} maxLength={64} autoComplete="new-password" value={form.password} onChange={set('password')} /></div>
        <button className="btn" style={{ width: '100%' }} disabled={state.busy}>{state.busy ? 'Creating…' : 'Register'}</button>
        <p className="center small" style={{ marginTop: '1rem', marginBottom: 0 }}>Already registered? <Link to="/login">Login</Link></p>
      </form>
    </div>
  );
}
