const BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8001').replace(/\/$/, '');

let token = null;
try { token = localStorage.getItem('token'); } catch { /* storage unavailable */ }

export function setToken(t) {
  token = t;
  try {
    if (t) localStorage.setItem('token', t); else localStorage.removeItem('token');
  } catch { /* ignore */ }
}
export const hasToken = () => Boolean(token);

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

function errorMessage(data, status) {
  const d = data?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) {
    return d.map((e) => `${(e.loc || []).filter((p) => p !== 'body').join('.')}: ${e.msg}`).join('; ');
  }
  if (status === 429) return 'Too many requests. Please wait a moment and try again.';
  return `Request failed (${status})`;
}

/** json: object body; form: FormData body (multipart). */
export async function api(path, { method = 'GET', json, form } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let body;
  if (json !== undefined) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(json); }
  else if (form) body = form;

  let res;
  try {
    res = await fetch(BASE + path, { method, headers, body });
  } catch {
    throw new ApiError('Cannot reach the server. Please check your connection and try again.', 0);
  }
  if (res.status === 401 && token && !path.startsWith('/api/auth/login')) {
    setToken(null);
    window.dispatchEvent(new Event('auth:expired'));
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(errorMessage(data, res.status), res.status);
  return data;
}

/** Attachments need the Authorization header, so fetch as a blob and open it. */
export async function openAttachment(ref, att) {
  const res = await fetch(`${BASE}/api/grievances/${ref}/attachments/${att.id}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new ApiError('Could not download the attachment', res.status);
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement('a');
  a.href = url;
  a.target = '_blank';
  a.rel = 'noopener';
  if (!att.content_type.startsWith('image/') && att.content_type !== 'application/pdf') a.download = att.filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}
