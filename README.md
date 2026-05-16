# GoalFlow — Goal Setting & Tracking Portal

**AtomQuest Hackathon 2026 Submission**

A production-grade, role-based Goal Setting & Tracking Portal built to satisfy all mandatory BRD requirements of the AtomQuest Hackathon 1.0 problem statement.

---

## Features

### Mandatory BRD Features
- **Goal Creation** — Up to 8 goals per employee with Thrust Area, Title, Description, UoM, Target, Weightage
- **Validation Rules** — Max 8 goals, min 10% per goal, total weightage must equal 100%
- **Goal Submission Workflow** — Employee submits → Manager reviews → Approves or Returns
- **Goal Locking** — Goals locked on approval; only Admin can unlock
- **Shared Goals** — Admin pushes departmental KPIs to multiple employees
- **Quarterly Achievement Updates** — Employees log actuals per quarter
- **Progress Calculation Engine** — Min, Max, Timeline, Zero-based UoM formulas
- **Manager Check-Ins** — Structured 4-field templates (Wins, Risks, Support, Next Steps)
- **Reports** — Achievement report with CSV export; Completion dashboard
- **Audit Trail** — All post-lock changes logged with actor, field, old/new values
- **Cycle Management** — Admin opens/closes goal-setting and check-in windows

### Differentiators
- **Goal Weightage Meter** — Live progress bar during goal creation
- **Goal Creation Wizard** — 3-step guided flow (Add → Preview → Submit)
- **Goal Health Indicators** — Healthy / Watch / At Risk per goal
- **Manager Attention Dashboard** — Action-oriented cards (pending, overdue, at-risk)
- **Approval Comparison View** — Highlights manager edits vs. original submission
- **Structured Check-In Template** — Consistent 4-section comment format
- **Cycle Countdown Banner** — "X days remaining" visible on every page
- **Unlock History Badge** — Shows lock/unlock history per goal sheet
- **Quarterly Trend Charts** — Q1–Q4 progress visualization (Chart.js)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI |
| Frontend | Jinja2 + HTML/CSS/Vanilla JS |
| Database | SQLite (via SQLAlchemy ORM) |
| Charts | Chart.js (CDN) |
| Auth | Session cookies + itsdangerous + bcrypt |
| Hosting | Render (free tier) |
| Version Control | Git + GitHub |

---

## Local Setup

### Prerequisites
- Python 3.11+
- pip

### Steps

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd goalflow

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application (auto-seeds on first run)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 5. Open in browser
# http://localhost:8000
```

---

## Demo Credentials

| Role | Email | Password |
|---|---|---|
| Admin / HR | admin@demo.com | demo123 |
| Manager (Engineering) | manager@demo.com | demo123 |
| Manager (Operations) | manager2@demo.com | demo123 |
| Employee | employee@demo.com | demo123 |
| Employee 2 | employee2@demo.com | demo123 |

---

## Project Structure

```
goalflow/
├── main.py                 # App entry point
├── requirements.txt
├── render.yaml             # Render deployment config
├── app/
│   ├── database.py         # SQLite engine + session
│   ├── models.py           # SQLAlchemy ORM models
│   ├── auth.py             # Password hashing + session cookies
│   ├── dependencies.py     # Role-based access guards
│   ├── seed.py             # Demo data seeder
│   ├── routers/
│   │   ├── auth.py
│   │   ├── employee.py
│   │   ├── manager.py
│   │   └── admin.py
│   └── services/
│       ├── progress.py     # UoM calculation engine
│       └── audit.py        # Audit log writer
├── templates/
│   ├── base.html           # Master layout
│   ├── login.html
│   ├── employee/
│   ├── manager/
│   └── admin/
└── static/
    ├── css/styles.css
    └── js/
        ├── utils.js
        ├── weightage_meter.js
        └── charts.js
```

---

## Architecture

```
Browser → FastAPI (Uvicorn) → Business Logic → SQLite Database
                           → Jinja2 Templates → HTML/CSS/JS → Chart.js
```

**Cost Optimisation:** Single-service architecture with SQLite and Render free tier.
Operational cost: ~$0/month.

---

## Live URL

> **[https://goalflow.onrender.com](https://goalflow.onrender.com)**
> *(Update after deployment)*

---

## Future Scope

- Microsoft Entra ID (Azure AD) SSO
- Email / Teams notifications
- Escalation workflows
- Full org hierarchy import
