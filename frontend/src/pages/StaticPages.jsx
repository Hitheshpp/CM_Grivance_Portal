import { Link } from 'react-router-dom';

export function About() {
  return (
    <div className="container" style={{ maxWidth: 900 }}>
      <h1>About Us</h1>
      <div className="alert warn">This is a recruitment prototype used to demonstrate an engineering solution. It is not an
        official portal and is not affiliated with or endorsed by the Government of Kerala or the CMO.</div>
      <div className="card"><h2>Purpose</h2>
        <p>To give citizens one dependable channel to raise grievances about public infrastructure, healthcare, education and
          other public services – and to give the Chief Minister's Office a clear, accountable way to route and monitor action.</p></div>
      <div className="card"><h2>Vision</h2>
        <p>A responsive administration where every citizen's concern is acknowledged, acted upon and closed with a transparent
          explanation.</p></div>
      <div className="card"><h2>Mission</h2>
        <p>To make grievance redressal simple to access, fast to route, and open to scrutiny, by combining a clear workflow, an
          audit trail for every action and responsible use of AI to assist human decision-makers.</p></div>
      <div className="card"><h2>Objectives</h2>
        <ul>
          <li>Provide a single online window to submit and track grievances with a unique reference number.</li>
          <li>Route each grievance to the correct department and officer quickly.</li>
          <li>Monitor delays and escalate overdue cases automatically visible to the CMO.</li>
          <li>Record every status change with the responsible user and time for full traceability.</li>
          <li>Close the loop with citizens: share outcomes, collect feedback and allow reopening.</li>
          <li>Use AI only as an advisor – humans make all official decisions.</li>
        </ul></div>
    </div>
  );
}

const STEPS = [
  ['Citizen submits a grievance', 'Register, log in and fill in the district, category, subject and description. You may attach one image or PDF. The AI assistant can suggest a category and priority for you to review.'],
  ['Reference ID is generated', 'A unique number (e.g. KGR-2026-000123) is issued instantly. Use it to track progress at any time.'],
  ['CMO review', 'The CMO team reviews the grievance, confirms or corrects the AI-suggested category and priority, and adds internal notes if needed.'],
  ['Forwarded to the department', 'The CMO assigns the grievance to the relevant department and, optionally, a named officer.'],
  ['Officer investigates', 'The officer reviews details and attachments, marks the grievance In Progress and adds remarks you can see.'],
  ['Action-taken report', 'The department submits an action-taken report back to the CMO.'],
  ['CMO reviews the response', 'The CMO accepts the report (grievance becomes Resolved) or sends it back for more work.'],
  ['Resolved or reopened', 'You see the outcome, can rate the resolution, and may reopen the grievance with a reason if the problem persists.'],
];

export function HowItWorks() {
  return (
    <div className="container" style={{ maxWidth: 900 }}>
      <h1>How It Works</h1>
      <p className="muted">Every grievance follows the same traceable path. Statuses used: Submitted → Under Review → In Progress → Resolved (or Reopened).</p>
      {STEPS.map(([t, d], i) => (
        <div className="card" key={t} style={{ display: 'flex', gap: '1rem' }}>
          <div className="step" style={{ minWidth: 44 }}><div className="n">{i + 1}</div></div>
          <div><h3>{t}</h3><p style={{ margin: 0 }}>{d}</p></div>
        </div>
      ))}
      <p className="center" style={{ marginTop: '1.5rem' }}>
        <Link className="btn large" to="/citizen/submit">Submit a Grievance</Link>
      </p>
    </div>
  );
}

const FAQS = [
  ['Who can submit a grievance?', 'Any registered citizen. Registration needs your name, email, mobile number and a password.'],
  ['How do I submit a grievance?', 'Log in, choose Submit Grievance, select the district and category, write a subject and detailed description and optionally attach an image or PDF (max 5 MB).'],
  ['What is the reference number?', 'A unique ID such as KGR-2026-000123 generated when you submit. Keep it safe – it is how you track your grievance.'],
  ['How can I track my grievance?', 'Use the Track page and enter the reference number, or log in and open your dashboard for full details and updates.'],
  ['What do the statuses mean?', 'Submitted: received. Under Review: being reviewed or routed by the CMO. In Progress: the department is acting. Resolved: action accepted by the CMO. Reopened: you reported the issue still exists.'],
  ['How long does resolution take?', 'Target timelines depend on priority (High 7 days, Medium 15 days, Low 30 days in this prototype). Overdue cases are visible to the CMO and can be escalated.'],
  ['What does the AI assistant do?', 'It reads your description and suggests a category, priority, department and summary, and flags possible duplicates. These are suggestions only; you and the CMO team review them.'],
  ['Can I reopen a resolved grievance?', 'Yes. If the problem persists, open the grievance and choose Reopen with a reason. A fresh timeline starts.'],
  ['Is this the official government portal?', 'No. This is a fictional recruitment prototype. Do not submit real grievances or real personal data.'],
];

export function FAQ() {
  return (
    <div className="container" style={{ maxWidth: 820 }}>
      <h1>Frequently Asked Questions</h1>
      {FAQS.map(([q, a]) => (
        <details className="faq" key={q}><summary>{q}</summary><div>{a}</div></details>
      ))}
    </div>
  );
}
