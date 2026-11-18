import { useEffect, useState } from 'react';
import { api } from '../api';

const slug = (s) => String(s).toLowerCase().replace(/\s+/g, '-');

export const StatusBadge = ({ status }) => <span className={`badge ${slug(status)}`}>{status}</span>;
export const PriorityBadge = ({ priority }) => <span className={`badge ${slug(priority)}`}>{priority}</span>;

const fmt = new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
const fmtDate = new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' });
export const formatDateTime = (d) => (d ? fmt.format(new Date(d)) : '–');
export const formatDate = (d) => (d ? fmtDate.format(new Date(d)) : '–');

export function Spinner({ label = 'Loading…' }) {
  return <p className="center muted" role="status"><span className="spinner" aria-hidden="true" /> {label}</p>;
}

export function Alert({ kind = 'error', children }) {
  if (!children) return null;
  return <div className={`alert ${kind}`} role={kind === 'error' ? 'alert' : 'status'}>{children}</div>;
}

export function Timeline({ items, showActorName = false }) {
  if (!items?.length) return <p className="muted">No history yet.</p>;
  return (
    <ol className="timeline">
      {items.map((h, i) => (
        <li key={h.id ?? i} className={h.visibility && h.visibility !== 'public' ? 'private' : ''}>
          <div className="when">
            {formatDateTime(h.created_at)} · {showActorName && h.actor_name ? `${h.actor_name} (${h.actor_role})` : h.actor_role}
            {h.visibility && h.visibility !== 'public' && <> · <strong>{h.visibility === 'internal' ? 'CMO internal' : 'Department only'}</strong></>}
          </div>
          <div className="what">{h.action} {h.to_status !== h.from_status && <StatusBadge status={h.to_status} />}</div>
          {h.remarks && <div className="remark">{h.remarks}</div>}
        </li>
      ))}
    </ol>
  );
}

export function Pagination({ page, pageSize, total, onChange }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages <= 1) return null;
  return (
    <div className="pagination">
      <button className="btn secondary small" disabled={page <= 1} onClick={() => onChange(page - 1)}>Previous</button>
      <span className="small muted">Page {page} of {pages} ({total} records)</span>
      <button className="btn secondary small" disabled={page >= pages} onClick={() => onChange(page + 1)}>Next</button>
    </div>
  );
}

/** Loads districts/categories/etc. once per page load. */
let metaPromise;
export function useMeta() {
  const [meta, setMeta] = useState(null);
  useEffect(() => {
    metaPromise = metaPromise || api('/api/public/meta');
    metaPromise.then(setMeta).catch(() => { metaPromise = null; });
  }, []);
  return meta;
}

/** Generic data loader hook. */
export function useFetch(path, deps = []) {
  const [state, setState] = useState({ data: null, error: '', loading: true });
  useEffect(() => {
    let live = true;
    setState((s) => ({ ...s, loading: true, error: '' }));
    api(path)
      .then((data) => live && setState({ data, error: '', loading: false }))
      .catch((e) => live && setState({ data: null, error: e.message, loading: false }));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, ...deps]);
  return state;
}
