import { Alert, Spinner, useFetch } from '../components/ui';

export default function Departments() {
  const { data, error, loading } = useFetch('/api/public/departments');
  return (
    <div className="container">
      <h1>Departments</h1>
      <p className="muted">Sample (fictional) departments to which grievances can be forwarded.</p>
      {loading && <Spinner />}
      <Alert>{error}</Alert>
      <div className="grid cols-3">
        {(data || []).map((d) => (
          <div className="card dept-card" key={d.id}><span className="tag">{d.category}</span><h3>{d.name}</h3><p>{d.description}</p></div>
        ))}
      </div>
    </div>
  );
}
