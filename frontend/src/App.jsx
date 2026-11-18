import { useEffect } from 'react';
import { Link, Route, Routes, useLocation } from 'react-router-dom';
import { Layout, RequireRole } from './components/Layout';
import { About, FAQ, HowItWorks } from './pages/StaticPages';
import Home from './pages/Home';
import Departments from './pages/Departments';
import Contact from './pages/Contact';
import Track from './pages/Track';
import { Login, Register } from './pages/AuthPages';
import CitizenDashboard from './pages/citizen/Dashboard';
import SubmitGrievance from './pages/citizen/Submit';
import GrievanceDetail from './pages/GrievanceDetail';
import CmoDashboard from './pages/cmo/Dashboard';
import OfficerDashboard from './pages/officer/Dashboard';

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
}

const NotFound = () => (
  <div className="container center"><h1>Page not found</h1><p><Link to="/">Back to home</Link></p></div>
);

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="about" element={<About />} />
          <Route path="how-it-works" element={<HowItWorks />} />
          <Route path="departments" element={<Departments />} />
          <Route path="contact" element={<Contact />} />
          <Route path="faq" element={<FAQ />} />
          <Route path="track" element={<Track />} />
          <Route path="track/:ref" element={<Track />} />
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />

          <Route path="citizen" element={<RequireRole roles={['citizen']}><CitizenDashboard /></RequireRole>} />
          <Route path="citizen/submit" element={<RequireRole roles={['citizen']}><SubmitGrievance /></RequireRole>} />
          <Route path="grievances/:ref" element={<RequireRole><GrievanceDetail /></RequireRole>} />
          <Route path="cmo" element={<RequireRole roles={['cmo']}><CmoDashboard /></RequireRole>} />
          <Route path="officer" element={<RequireRole roles={['officer']}><OfficerDashboard /></RequireRole>} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </>
  );
}
