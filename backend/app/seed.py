"""Fictional demo data. Run automatically on first start (SEED_ON_STARTUP=true) or: python -m app.seed

All people, emails and complaints are invented for this recruitment prototype.
"""
import random
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .constants import DISTRICTS, SLA_DAYS
from .models import (ContactEnquiry, Department, DepartmentAssignment, Feedback, Grievance, GrievanceHistory,
                     User, utcnow)
from .security import hash_password

DEMO_PASSWORD = "Demo@1234"

DEPARTMENTS = [
    ("PWD", "Public Works Department", "Roads, bridges and government buildings.", "Roads & Infrastructure"),
    ("HEALTH", "Health & Family Welfare", "Public hospitals, primary health centres and public health programmes.", "Healthcare"),
    ("EDU", "General Education", "Government schools, teachers, scholarships and exams.", "Education"),
    ("WATER", "Water Resources & Sanitation", "Drinking water supply, sewerage and sanitation.", "Water & Sanitation"),
    ("POWER", "Electricity Board", "Power supply, outages, meters and street lighting.", "Electricity"),
    ("LSGD", "Local Self Government", "Panchayats, municipalities, waste management and local services.", "Public Services"),
    ("HOME", "Home Department", "Law and order, police services and public safety.", "Law & Order"),
    ("SJD", "Social Justice", "Pensions, disability support, elderly and child welfare.", "Social Welfare"),
    ("AGRI", "Agriculture", "Farmer support, irrigation, crop insurance and inputs.", "Agriculture"),
    ("ENV", "Forest & Environment", "Forests, wildlife, pollution control and environment.", "Environment"),
]

CITIZENS = [("Anjali Menon", "9400000001"), ("Rahul Nair", "9400000002"), ("Fathima Beevi", "9400000003"),
            ("Joseph Thomas", "9400000004"), ("Divya Krishnan", "9400000005")]

# (department code, category, subject, description, priority)
TEMPLATES = [
    ("PWD", "Roads & Infrastructure", "Large potholes on main road near bus stand",
     "The main road near the bus stand has several deep potholes that fill with water during rain. Two-wheeler riders have already fallen and it is dangerous for school children walking in the morning. Please repair the road urgently.", "High"),
    ("PWD", "Roads & Infrastructure", "Damaged footpath and open drain cover",
     "The footpath outside the market is broken and a drain cover is missing, creating a serious hazard for pedestrians especially the elderly. This has been pending for several months.", "Medium"),
    ("HEALTH", "Healthcare", "No doctor available at primary health centre in the evenings",
     "The primary health centre in our ward has no doctor after 2 PM and patients are sent to the district hospital which is 25 km away. Please arrange evening duty doctors for emergencies.", "High"),
    ("HEALTH", "Healthcare", "Shortage of essential medicines at taluk hospital",
     "Patients at the taluk hospital are told to buy basic medicines like antibiotics and diabetes tablets from outside pharmacies, which poor families cannot afford. Please ensure regular medicine stock.", "Medium"),
    ("EDU", "Education", "Government school building leaking and unsafe classrooms",
     "The roof of the upper primary school building leaks heavily and parts of the ceiling plaster have fallen in two classrooms. Children are at risk and classes are being disrupted during monsoon.", "High"),
    ("EDU", "Education", "Scholarship amount not received for last academic year",
     "My daughter is eligible for the post-matric scholarship but the amount for the last academic year has not been credited even after submitting all documents on time. Please check the status of her application.", "Medium"),
    ("WATER", "Water & Sanitation", "No drinking water supply for ten days",
     "There has been no drinking water supply in our colony for the past ten days. Residents including infants and elderly people depend on expensive private tankers. Please restore supply immediately.", "High"),
    ("WATER", "Water & Sanitation", "Sewage overflowing onto the street",
     "Sewage from a blocked line is overflowing onto the street near the temple junction and causing a foul smell and mosquito breeding. Please clear the blockage and clean the area.", "Medium"),
    ("POWER", "Electricity", "Frequent power outages in the evening",
     "Our locality faces power cuts almost every evening for 2-3 hours. Students cannot study and small shops are losing business. Please inspect the transformer and fix the problem.", "Medium"),
    ("POWER", "Electricity", "Street lights not working on coastal road",
     "Around fifteen street lights on the coastal road have been off for over a month making the road unsafe for women and night workers. Please repair them.", "Low"),
    ("LSGD", "Public Services", "Garbage not collected from our ward for weeks",
     "Waste has not been collected from our ward for three weeks and garbage is piling up near the road, attracting stray dogs and spreading disease. Please resume regular collection.", "Medium"),
    ("LSGD", "Public Services", "Delay in issuing building permit",
     "I applied for a building permit for my small house four months ago and the application is still pending without any query raised. Please advise on the status and speed up the process.", "Low"),
    ("HOME", "Law & Order", "Repeated theft and harassment near bus stop at night",
     "There have been repeated incidents of chain snatching and harassment of women near the bus stop after 8 PM. Police patrolling is absent. Please increase night patrolling for public safety.", "High"),
    ("SJD", "Social Welfare", "Widow pension not received for six months",
     "My mother's widow pension has not been credited for six months and she depends entirely on it. We have submitted the life certificate. Please look into the matter.", "Medium"),
    ("AGRI", "Agriculture", "Crop damaged by flooding but compensation not paid",
     "Our paddy fields were submerged during the recent floods and the crop is completely lost. The compensation promised under crop insurance has not been paid even after the agriculture officer visited.", "Medium"),
    ("ENV", "Environment", "Factory discharging untreated waste into river",
     "A nearby unit is discharging dark untreated waste into the river at night. Fish are dying and families who use the river water are falling sick. Please inspect and take action.", "High"),
    ("PWD", "Roads & Infrastructure", "Bridge railing broken at river crossing",
     "The railing of the small bridge at the river crossing is broken and could cause a serious accident, particularly for children and cyclists. Please repair it.", "High"),
    ("EDU", "Education", "Request for additional teachers in higher secondary school",
     "Our higher secondary school has no teacher for physics and mathematics this year, affecting the preparation of students for board examinations. Please appoint teachers at the earliest.", "Medium"),
]

OFFICER_REPORTS = [
    "Site inspection was carried out and the issue was verified. Corrective work has been completed and the area re-inspected by the supervising engineer. Photographs and the work completion note are attached to the department file.",
    "The matter was investigated with the local office. Necessary action has been taken and the concerned parties were informed. The beneficiary has confirmed that the problem has been resolved.",
    "A team was deployed, the fault was rectified and preventive measures were put in place. Regular monitoring will be done for the next month to avoid recurrence.",
]


def _hist(db, g, action, frm, to, actor, when, remarks=None, vis="public"):
    db.add(GrievanceHistory(grievance=g, action=action, from_status=frm, to_status=to, remarks=remarks,
                            visibility=vis, actor_id=actor.id if actor else None,
                            actor_role=actor.role if actor else "system", created_at=when))


def seed(db: Session) -> None:
    rnd = random.Random(42)
    now = utcnow()
    pwd = hash_password(DEMO_PASSWORD)

    depts = {}
    for code, name, desc, cat in DEPARTMENTS:
        d = Department(code=code, name=name, description=desc, default_category=cat)
        db.add(d)
        depts[code] = d
    db.flush()

    cmo = User(name="CMO Administrator (Demo)", email="cmo@demo-portal.in", mobile="9400000000",
               password_hash=pwd, role="cmo")
    db.add(cmo)
    officers = {}
    for code, d in depts.items():
        o = User(name=f"{d.name.split(' ')[0]} Officer (Demo)", email=f"officer.{code.lower()}@demo-portal.in",
                 mobile="9400010000", password_hash=pwd, role="officer", department_id=d.id)
        db.add(o)
        officers[code] = o
    citizens = []
    for i, (name, mobile) in enumerate(CITIZENS, 1):
        c = User(name=name, email=f"citizen{i}@demo-portal.in", mobile=mobile, password_hash=pwd, role="citizen")
        db.add(c)
        citizens.append(c)
    db.flush()

    # status mix: weighted so the dashboard has a realistic spread, including overdue cases
    outcomes = ["Submitted"] * 4 + ["Under Review"] * 5 + ["In Progress"] * 8 + ["Resolved"] * 12 + ["Reopened"] * 2 \
        + ["ReportPending"] * 3
    for n in range(34):
        code, cat, subject, desc, prio = TEMPLATES[n % len(TEMPLATES)]
        if n >= len(TEMPLATES):
            subject = f"{subject} (ward {n % 9 + 1})"
        outcome = outcomes[n % len(outcomes)] if n >= 3 else ["Submitted", "In Progress", "Resolved"][n]
        citizen = citizens[n % len(citizens)]
        created = now - timedelta(days=rnd.randint(2, 55), hours=rnd.randint(0, 20))
        g = Grievance(citizen_id=citizen.id, district=DISTRICTS[(n * 5) % len(DISTRICTS)], category=cat,
                      subject=subject, description=desc, priority=prio, status="Submitted",
                      due_date=created + timedelta(days=SLA_DAYS[prio]), created_at=created, updated_at=created,
                      ai_department_id=depts[code].id, ai_category=cat, ai_priority=prio,
                      ai_summary=desc.split(". ")[0][:280], ai_provider="seed-data", ai_is_fallback=True,
                      ai_duplicates=[])
        db.add(g)
        db.flush()
        g.reference_no = f"KGR-{created.year}-{g.id:06d}"
        t = created
        _hist(db, g, "Grievance submitted", None, "Submitted", citizen, t, "Grievance registered by citizen")
        if outcome != "Submitted":
            t += timedelta(hours=rnd.randint(4, 30))
            g.status = "Under Review"
            _hist(db, g, "CMO review started", "Submitted", "Under Review", cmo, t)
            g.department_id, g.assigned_officer_id = depts[code].id, officers[code].id
            db.add(DepartmentAssignment(grievance=g, department_id=depts[code].id, officer_id=officers[code].id,
                                        assigned_by=cmo.id, note="Please investigate and report.", assigned_at=t))
            _hist(db, g, f"Forwarded to {depts[code].name}", "Under Review", "Under Review", cmo, t,
                  f"Officer: {officers[code].name}. Please investigate and report.")
            _hist(db, g, "CMO reviewed AI triage", "Under Review", "Under Review", cmo, t,
                  "AI suggestion confirmed without changes.", "department")
        if outcome in ("In Progress", "Resolved", "Reopened", "ReportPending"):
            t += timedelta(hours=rnd.randint(6, 48))
            g.status = "In Progress"
            _hist(db, g, "Status changed to In Progress", "Under Review", "In Progress", officers[code], t,
                  "Site visit scheduled; collecting details from the local office.")
        if outcome == "ReportPending":
            t += timedelta(days=1)
            g.report_text, g.report_status, g.report_submitted_at = OFFICER_REPORTS[n % 3], "Pending CMO Review", t
            _hist(db, g, "Action-taken report submitted to CMO", "In Progress", "In Progress", officers[code], t,
                  "Awaiting CMO review")
        if outcome in ("Resolved", "Reopened"):
            t += timedelta(days=rnd.randint(1, 4))
            g.report_text, g.report_submitted_at = OFFICER_REPORTS[n % 3], t
            _hist(db, g, "Action-taken report submitted to CMO", "In Progress", "In Progress", officers[code], t,
                  "Awaiting CMO review")
            t += timedelta(hours=10)
            g.status, g.report_status, g.resolved_at = "Resolved", "Accepted", t
            _hist(db, g, "Resolved: report accepted by CMO", "In Progress", "Resolved", cmo, t,
                  "Action-taken report accepted")
            if outcome == "Resolved" and n % 2 == 0:
                db.add(Feedback(grievance=g, citizen_id=citizen.id, rating=rnd.randint(3, 5),
                                comment="Issue was fixed. Thank you.", created_at=t + timedelta(days=1)))
        if outcome == "Reopened":
            t += timedelta(days=2)
            g.status, g.resolved_at, g.report_status = "Reopened", None, None
            g.due_date = t + timedelta(days=SLA_DAYS[prio])
            _hist(db, g, "Status changed to Reopened", "Resolved", "Reopened", citizen, t,
                  "The problem has returned after a few days.")
        g.updated_at = t

    db.add_all([
        ContactEnquiry(name="Sample Visitor", email="visitor@demo-portal.in", subject="How do I track my complaint?",
                       message="I submitted a grievance last week and would like to know how to follow its progress."),
    ])
    db.commit()


if __name__ == "__main__":
    from .database import Base, SessionLocal, engine
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        if s.scalar(select(User).limit(1)):
            print("Database already has data; skipping seed.")
        else:
            seed(s)
            print("Seeded fictional demo data. Demo password for all accounts:", DEMO_PASSWORD)
