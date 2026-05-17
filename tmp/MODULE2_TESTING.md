# Module 2 — Manual Testing Instructions

## Setup
```bash
pip install -r requirements.txt
rm -f goalflow.db          # fresh start
uvicorn main:app --reload  # auto-seeds on first run
# Open: http://localhost:8000
```

## Demo Credentials
| Role     | Email               | Password |
|----------|---------------------|----------|
| Employee | employee@demo.com   | demo123  |
| Employee | employee2@demo.com  | demo123  |

---

## Test Flows

### Flow 1 — Happy Path (Goal Creation & Submission)
1. Login as `employee@demo.com`
2. Click **My Goals** → click **Go to wizard** or **+ Create My Goals**
3. Observe **Weightage Meter** shows `0% allocated` (yellow)
4. Add a goal:
   - Thrust Area: `Revenue`
   - Title: `Achieve Q1 Target`
   - Description: `Hit ₹10Cr by June`
   - UoM: `Higher is Better (Min)`
   - Target: `10000000`
   - Weightage: `40`
5. Click **+ Add Goal** — goal appears in table, meter shows `40%` (yellow)
6. Add two more goals (35% + 25%) → meter turns **green at 100%**
7. Click **Preview & Validate →** (Step 2)
   - All 3 validation checks show ✓ green
8. Click **Proceed to Submit →** (Step 3)
   - Review confirmation summary
9. Click **✓ Submit for Manager Approval**
10. Redirected to **My Goals** — status badge shows `Submitted`

### Flow 2 — Edit Goal
1. On Step 1 wizard, click **✎** on any goal row
2. Edit modal opens with pre-filled fields
3. Change the title and weightage, click **Save Changes**
4. Table and meter update with new values

### Flow 3 — Delete Goal
1. On Step 1 wizard, click **✕** on any goal
2. Confirm dialog appears
3. Goal removed, meter adjusts

### Flow 4 — Validation Enforcement
| Action | Expected Result |
|--------|----------------|
| Add goal with 5% weightage | Error: min 10% |
| Submit with total < 100% | Error: must be 100% |
| Submit with total > 100% | Error: must be 100% |
| Try to add 9th goal | Error: max 8 goals |
| Access wizard after submission | Redirect to My Goals |

### Flow 5 — Cross-User Security
1. Login as `employee2@demo.com`
2. Manually navigate to `/employee/goals/{id}/delete` for employee1's goal
3. Expected: Error redirect (access denied)

---

## Automated Test Suite
```bash
cd goalflow
rm -f goalflow.db
python -c "from app.database import init_db; init_db(); from app.seed import seed; seed()"
python -m pytest tests/test_module2.py -v   # or run the inline test script
```
All 20 tests must pass: T01–T20.

---

## Files Changed in Module 2

| File | Change |
|------|--------|
| `app/routers/employee.py` | Full implementation — 8 endpoints |
| `templates/employee/dashboard.html` | Real data: sheet status, goals table |
| `templates/employee/my_goals.html` | Full read-only goal sheet view |
| `templates/employee/goal_wizard.html` | 3-step wizard + edit modal |
| `static/css/styles.css` | Added wizard, modal, validation styles |
| `static/js/weightage_meter.js` | Rewritten — data-attribute based meter |

No model changes — schema was correct from Phase 0.
