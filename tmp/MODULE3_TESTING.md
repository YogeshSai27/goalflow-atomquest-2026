# Module 3 — Manager Approval Workflow
## Manual Testing Instructions

---

## Setup

```bash
pip install -r requirements.txt
rm -f goalflow.db
uvicorn main:app --reload
# Open: http://localhost:8000
```

## Demo Credentials

| Role     | Email                | Password | Direct Reports             |
|----------|----------------------|----------|----------------------------|
| Manager  | manager@demo.com     | demo123  | employee@, employee2@      |
| Manager  | manager2@demo.com    | demo123  | employee3@, employee4@     |
| Employee | employee@demo.com    | demo123  | (reports to manager@)      |
| Employee | employee3@demo.com   | demo123  | (reports to manager2@)     |

**Pre-condition:** At least one employee must have submitted a goal sheet.
Use Module 2 flow first, or follow Step 0 below.

---

## Step 0 — Create a Submitted Goal Sheet (Pre-condition)

1. Login as `employee@demo.com`
2. Navigate to **My Goals → Go to Wizard**
3. Add 3 goals totalling exactly 100% weightage
4. Click through to **Step 3 → Submit for Manager Approval**
5. Confirm status shows **Submitted** on My Goals page
6. Logout

---

## Test Flows

### Flow 1 — Manager Attention Dashboard

1. Login as `manager@demo.com`
2. Navigate to **Dashboard**
3. Verify:
   - **Pending Approval** card shows count ≥ 1
   - **Action Required** table lists the submitted employee
   - **Team Goal Sheet Status** table shows all direct reports
   - Click **Review** button → lands on approval detail page

---

### Flow 2 — Approvals List with Tab Filtering

1. Login as `manager@demo.com`
2. Navigate to **Approvals**
3. Verify **Pending** tab is active and shows submitted sheet(s)
4. Click **Returned** tab → empty state message
5. Click **Approved** tab → empty state message
6. Click **All** tab → all sheets visible

---

### Flow 3 — Goal Sheet Review Page

1. From Approvals list, click **Review** on a submitted sheet
2. Verify:
   - Employee name, department, submitted date visible in header
   - All goals listed in table with thrust area, title, UoM, target, weightage
   - Validation checklist shows ✓ green if all rules pass
   - **Approve** and **Return** panels both visible at bottom

---

### Flow 4 — Inline Goal Edit

1. On the Review page, click the **✎** edit button on any goal row
2. An inline edit row appears with pre-filled target and weightage inputs
3. Change the **Target Value** (e.g. 10000000 → 12000000)
4. Click ✓ to save
5. Verify:
   - Success flash message appears
   - Updated value visible in the table
   - **Escape** key closes the edit row without saving

**Validation:**
| Action | Expected |
|--------|----------|
| Set weightage to 5% | Error: minimum 10% |
| Set negative target | Error: cannot be negative |

---

### Flow 5 — Approve Goal Sheet

1. On the Review page (submitted sheet with all validations passing):
2. In the **Approve** panel, optionally type a comment
3. Click **✓ Approve & Lock**
4. Confirm dialog → click OK
5. Verify:
   - Redirected to Approvals list with success message
   - Sheet moves to **Approved** tab
   - Login as employee → wizard redirects (sheet is locked)
   - Dashboard **Approved** count increments

---

### Flow 6 — Return for Revision

1. Submit a second employee's goal sheet (login as `employee3@demo.com`)
2. Login as `manager2@demo.com`
3. Open the submitted sheet
4. In the **Return** panel, type: *"Please revise the cost reduction target"*
5. Click **↩ Return for Revision** → confirm
6. Verify:
   - Redirected to Approvals list with success message
   - Sheet moves to **Returned** tab
   - Login as `employee3@demo.com` → wizard is accessible again
   - Return reason shown as a red banner on the wizard

**Validation:**
| Action | Expected |
|--------|----------|
| Return with blank reason | Error: reason required |
| Approve already-approved sheet | Error: wrong status |

---

### Flow 7 — Cross-Manager Security

1. Login as `manager@demo.com`
2. Manually navigate to a sheet belonging to `manager2`'s employee
   (e.g. `/manager/approvals/3` if sheet id=3 belongs to emp3)
3. Expected: redirect with "Access denied" error

---

## Validation Rules Enforced

| Rule | Enforced At |
|------|-------------|
| Goal weightage ≥ 10% | Inline edit POST (backend) |
| Total weightage = 100% | Approve POST (backend) + UI checklist |
| Return reason required | Return POST (backend + HTML required attr) |
| Only submitted sheets can be approved | Approve POST (backend) |
| Only submitted sheets can be returned | Return POST (backend) |
| Manager can only see own direct reports | All endpoints (backend query filter) |

---

## Files Changed in Module 3

| File | Change |
|------|--------|
| `app/models.py` | Added `manager_comments` + `return_reason` columns to GoalSheet |
| `app/database.py` | Added `_migrate()` helper for safe ALTER TABLE on existing DBs |
| `app/routers/manager.py` | Full implementation — 6 endpoints |
| `templates/manager/dashboard.html` | Attention dashboard with stat cards + action table |
| `templates/manager/pending_approvals.html` | Filterable approvals list with tab bar |
| `templates/manager/approval_detail.html` | Review page with inline edit rows + approve/return panel |
| `static/css/styles.css` | Appended: info-grid, tab-bar, action-panel styles |

No new JS files — all interactivity is inline `<script>` in the detail template.

---

## Automated Test Results

22/22 tests passed (T01–T22):
- T01–T04: Dashboard and list rendering
- T05–T07: Detail page access control
- T08–T10: Inline goal edit + audit log + validation
- T11–T15: Approve flow + DB state + audit + double-approve guard
- T16–T20: Return flow + DB state + audit + blank reason guard
- T21–T22: Post-workflow dashboard and tab correctness
