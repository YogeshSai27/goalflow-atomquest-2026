"""
seed.py — Seeds the database with demo users and an active cycle.

Run once:
    python -m app.seed

Creates:
    1 Admin
    2 Managers (Engineering, Operations)
    4 Employees (2 per manager)
    2 Cycles: one active goal_setting, one active q1
"""

from datetime import datetime, date
from app.database import SessionLocal, init_db
from app.auth import hash_password
from app.models import User, Cycle


# ---------------------------------------------------------------------------
# Demo credentials (match the blueprint spec)
# ---------------------------------------------------------------------------
DEMO_USERS = [
    # Admin
    {
        "name": "Admin User",
        "email": "admin@demo.com",
        "password": "demo123",
        "role": "admin",
        "department": "HR",
        "manager_id": None,
    },
    # Managers
    {
        "name": "Alice Manager",
        "email": "manager@demo.com",
        "password": "demo123",
        "role": "manager",
        "department": "Engineering",
        "manager_id": None,   # will be linked after insert
    },
    {
        "name": "Bob Manager",
        "email": "manager2@demo.com",
        "password": "demo123",
        "role": "manager",
        "department": "Operations",
        "manager_id": None,
    },
    # Employees under Alice
    {
        "name": "Carol Employee",
        "email": "employee@demo.com",
        "password": "demo123",
        "role": "employee",
        "department": "Engineering",
        "manager_email": "manager@demo.com",
    },
    {
        "name": "Dave Employee",
        "email": "employee2@demo.com",
        "password": "demo123",
        "role": "employee",
        "department": "Engineering",
        "manager_email": "manager@demo.com",
    },
    # Employees under Bob
    {
        "name": "Eve Employee",
        "email": "employee3@demo.com",
        "password": "demo123",
        "role": "employee",
        "department": "Operations",
        "manager_email": "manager2@demo.com",
    },
    {
        "name": "Frank Employee",
        "email": "employee4@demo.com",
        "password": "demo123",
        "role": "employee",
        "department": "Operations",
        "manager_email": "manager2@demo.com",
    },
]

DEMO_CYCLES = [
    {
        "name": "FY 2026-27 — Goal Setting",
        "type": "goal_setting",
        "start_date": "2026-05-01",
        "end_date": "2026-06-30",
        "is_active": True,
    },
    {
        "name": "FY 2026-27 — Q1 Check-In",
        "type": "q1",
        "start_date": "2026-07-01",
        "end_date": "2026-07-31",
        "is_active": False,
    },
    {
        "name": "FY 2026-27 — Q2 Check-In",
        "type": "q2",
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "is_active": False,
    },
    {
        "name": "FY 2026-27 — Q3 Check-In",
        "type": "q3",
        "start_date": "2027-01-01",
        "end_date": "2027-01-31",
        "is_active": False,
    },
    {
        "name": "FY 2026-27 — Q4 / Annual",
        "type": "q4",
        "start_date": "2027-03-01",
        "end_date": "2027-04-30",
        "is_active": False,
    },
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def seed():
    init_db()
    db = SessionLocal()

    try:
        # ----------------------------------------------------------------
        # Skip if already seeded
        # ----------------------------------------------------------------
        if db.query(User).count() > 0:
            print("⚠️  Database already seeded — skipping.")
            return

        print("🌱 Seeding database...")

        # ----------------------------------------------------------------
        # Insert users (first pass — no manager_id for employees yet)
        # ----------------------------------------------------------------
        inserted: dict[str, User] = {}

        for u in DEMO_USERS:
            user = User(
                name=u["name"],
                email=u["email"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
                department=u.get("department"),
                is_active=True,
            )
            db.add(user)
            db.flush()   # get the ID without committing
            inserted[u["email"]] = user

        # ----------------------------------------------------------------
        # Second pass — wire up manager_id for employees
        # ----------------------------------------------------------------
        for u in DEMO_USERS:
            if "manager_email" in u:
                emp = inserted[u["email"]]
                mgr = inserted[u["manager_email"]]
                emp.manager_id = mgr.id

        db.commit()

        # ----------------------------------------------------------------
        # Insert cycles
        # ----------------------------------------------------------------
        admin_user = inserted["admin@demo.com"]

        for c in DEMO_CYCLES:
            cycle = Cycle(
                name=c["name"],
                type=c["type"],
                start_date=c["start_date"],
                end_date=c["end_date"],
                is_active=c["is_active"],
                created_by=admin_user.id,
            )
            db.add(cycle)

        db.commit()

        # ----------------------------------------------------------------
        # Summary
        # ----------------------------------------------------------------
        print("\n✅ Seed complete!\n")
        print("Demo Credentials:")
        print("─" * 45)
        print(f"  Admin    → admin@demo.com       / demo123")
        print(f"  Manager  → manager@demo.com      / demo123")
        print(f"  Manager2 → manager2@demo.com     / demo123")
        print(f"  Employee → employee@demo.com     / demo123")
        print(f"  Employee2→ employee2@demo.com    / demo123")
        print(f"  Employee3→ employee3@demo.com    / demo123")
        print(f"  Employee4→ employee4@demo.com    / demo123")
        print("─" * 45)

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
