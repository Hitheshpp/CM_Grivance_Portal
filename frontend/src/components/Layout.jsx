import { useState } from 'react';
import { Link, NavLink, Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { HOME_BY_ROLE, useAuth } from '../auth';
import { Spinner } from './ui';

export function Layout() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const close = () => setOpen(false);

  return (
    <>
      <a className="skip-link" href="#content">Skip to main content</a>
      <div className="proto-banner" role="note">
        <strong>Recruitment prototype</strong> – built for a coding assessment. Not an official site; not affiliated with or
        endorsed by the Government of Kerala or the Chief Minister's Office. All data is fictional.
      </div>
      <header className="site">
        <div className="container nav-row">
          <Link to="/" className="brand" onClick={close}>
            <span className="logo" aria-hidden="true">G</span>
            <span>CM Grievance Portal<small>Public Grievance Redressal · Prototype</small></span>
          </Link>
          <button className="menu-toggle" aria-expanded={open} aria-controls="main-nav" onClick={() => setOpen(!open)}>
            <span className="sr-only">Toggle menu</span>☰
          </button>
          <nav id="main-nav" className={`main-nav ${open ? 'open' : ''}`} aria-label="Main" onClick={close}>
            <NavLink to="/" end>Home</NavLink>
            <NavLink to="/about">About Us</NavLink>
            <NavLink to="/how-it-works">How It Works</NavLink>
            <NavLink to="/departments">Departments</NavLink>
            <NavLink to="/faq">FAQ</NavLink>
            <NavLink to="/contact">Contact</NavLink>
            <NavLink to="/track">Track</NavLink>
            {user ? (
              <>
                <NavLink to={HOME_BY_ROLE[user.role]}>My Dashboard</NavLink>
                <button className="link" onClick={async () => { await logout(); navigate('/'); }}>
                  Logout ({user.name.split(' ')[0]})
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" state={{ from: pathname }}>Login</NavLink>
                <Link className="btn accent small" to="/register">Register</Link>
              </>
            )}
          </nav>
        </div>
      </header>
      <main id="content" tabIndex={-1}><Outlet /></main>
      <footer className="site">
        <div className="container">
          <div className="footer-grid">
            <div>
              <h4>CM Grievance Portal – Recruitment Prototype</h4>
              <p>A demonstration of a citizen grievance redressal workflow: submit, route, act, review and resolve.
                Built with FastAPI, PostgreSQL and React for the WhiteMatrix machine test.</p>
            </div>
            <div>
              <h4>Quick links</h4>
              <Link to="/register">Register</Link><Link to="/citizen/submit">Submit Grievance</Link>
              <Link to="/track">Track Grievance</Link><Link to="/faq">FAQ</Link>
            </div>
            <div>
              <h4>About</h4>
              <Link to="/about">About Us</Link><Link to="/how-it-works">How It Works</Link>
              <Link to="/departments">Departments</Link><Link to="/contact">Contact Us</Link>
            </div>
          </div>
          <div className="footer-note">
            This is a fictional prototype for evaluation only. It is not an official website and is not affiliated with,
            authorised or endorsed by the Government of Kerala or the Chief Minister's Office. Do not submit real
            personal data or real grievances.
          </div>
        </div>
      </footer>
    </>
  );
}

export function RequireRole({ roles, children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="container"><Spinner /></div>;
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to={HOME_BY_ROLE[user.role]} replace />;
  return children;
}
