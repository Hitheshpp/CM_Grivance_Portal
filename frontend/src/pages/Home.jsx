import { Link } from 'react-router-dom';
import { useFetch } from '../components/ui';
import { useAuth } from '../auth';

const STEPS = [
  ['Submit', 'Register and describe your grievance with an optional document or photo.'],
  ['CMO Review', 'The Chief Minister\'s Office reviews and triages every grievance.'],
  ['Assignment', 'It is forwarded to the responsible department and officer.'],
  ['Action', 'The officer investigates, updates progress and files an action-taken report.'],
  ['Resolution', 'The CMO reviews the report; you receive the outcome and can give feedback or reopen.'],
];

export default function Home() {
  const { user } = useAuth();
  const stats = useFetch('/api/public/stats').data;
  const depts = useFetch('/api/public/departments').data;

  return (
    <>
      <section className="hero" style={{ marginTop: '-1.8rem' }}>
        <div className="container">
          <h1>Your voice, heard at the highest level.</h1>
          <p>Submit a grievance to the Chief Minister's Office, track every step of its journey to the right department,
            and receive a transparent outcome. (Demonstration portal – fictional data.)</p>
          <div className="btn-row" style={{ marginTop: '1.4rem' }}>
            <Link className="btn accent large" to={user?.role === 'citizen' || !user ? '/citizen/submit' : '/'}>Submit Grievance</Link>
            <Link className="btn secondary large" to="/track">Track Grievance</Link>
          </div>
        </div>
      </section>

      <div className="container hero-stats">
        <div className="grid cols-4" aria-label="Portal statistics">
          <div className="card stat"><div className="num">{stats?.total_grievances ?? '–'}</div><div className="lbl">Grievances received</div></div>
          <div className="card stat"><div className="num">{stats?.resolved ?? '–'}</div><div className="lbl">Resolved</div></div>
          <div className="card stat"><div className="num">{stats ? `${stats.resolution_rate}%` : '–'}</div><div className="lbl">Resolution rate</div></div>
          <div className="card stat"><div className="num">{stats?.departments ?? '–'}</div><div className="lbl">Departments connected</div></div>
        </div>
        <p className="muted small center" style={{ marginTop: '.5rem' }}>Statistics are computed from the demo database (sample data).</p>
      </div>

      <section className="container section">
        <div className="section-title"><h2>How it works</h2><p>Five transparent steps from complaint to resolution.</p></div>
        <div className="grid cols-4" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))' }}>
          {STEPS.map(([t, d], i) => (
            <div className="card step" key={t}><div className="n">{i + 1}</div><h3>{t}</h3><p className="muted small">{d}</p></div>
          ))}
        </div>
      </section>

      <section className="container section">
        <div className="section-title"><h2>Featured departments</h2><p>Grievances are routed to the department best placed to act.</p></div>
        <div className="grid cols-3">
          {(depts || []).slice(0, 6).map((d) => (
            <div className="card dept-card" key={d.id}><span className="tag">{d.category}</span><h3>{d.name}</h3><p>{d.description}</p></div>
          ))}
        </div>
        <p className="center" style={{ marginTop: '1rem' }}><Link to="/departments">View all departments →</Link></p>
      </section>

      <section className="container section">
        <div className="card" style={{ background: 'var(--primary-soft)' }}>
          <h2>AI-assisted, human-decided</h2>
          <p style={{ marginBottom: 0 }}>When you describe your problem, an AI assistant suggests a category, priority and the
            likely department, and flags possible duplicates. These are only suggestions – you review them before submitting,
            and the CMO team makes every official decision.</p>
        </div>
      </section>
    </>
  );
}
