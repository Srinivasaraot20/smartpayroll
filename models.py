import datetime
import os
import sqlite3
import logging
from werkzeug.security import generate_password_hash

DB_PATH = os.environ.get("PAYROLL_DB_PATH", "app.db")


# -------------------------
# Connection helpers
# -------------------------

def _get_con():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def _row_to_dict(row):
    return dict(row) if row is not None else None


# -------------------------
# Schema + seeding
# -------------------------

def init_db():
    con = _get_con()
    cur = con.cursor()

    # Users
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL,
            force_password_change INTEGER DEFAULT 0
        );
        """
    )

    # Employees
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            address TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            emergency_contact TEXT DEFAULT '',
            date_of_birth TEXT,
            date_joined TEXT NOT NULL,
            basic_salary REAL NOT NULL,
            status TEXT NOT NULL,
            uan_number TEXT DEFAULT NULL,
            esi_number TEXT DEFAULT NULL,
            pan_number TEXT DEFAULT NULL,
            aadhaar_number TEXT DEFAULT NULL,
            state TEXT DEFAULT 'Maharashtra',
            pf_status TEXT DEFAULT 'Active',
            esi_status TEXT DEFAULT 'Active',
            pt_status TEXT DEFAULT 'Active',
            gender TEXT DEFAULT 'Male',
            marital_status TEXT DEFAULT 'Single',
            blood_group TEXT DEFAULT 'O+',
            nationality TEXT DEFAULT 'Indian',
            alternate_phone TEXT DEFAULT '',
            employee_code TEXT DEFAULT '',
            branch TEXT DEFAULT 'Main Headquarters',
            reporting_manager TEXT DEFAULT 'Admin User',
            employee_type TEXT DEFAULT 'Full-Time',
            probation_status TEXT DEFAULT 'Confirmed',
            salary_structure TEXT DEFAULT 'Standard Class',
            bank_account TEXT DEFAULT '',
            ifsc_code TEXT DEFAULT '',
            pf_number TEXT DEFAULT '',
            tax_info TEXT DEFAULT 'Single Filer',
            avatar_url TEXT DEFAULT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )

    # Attendance
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            note TEXT,
            check_in TEXT,
            check_out TEXT,
            working_hours REAL,
            overtime_hours REAL,
            location TEXT DEFAULT 'Office',
            shift TEXT DEFAULT 'General',
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE,
            UNIQUE(employee_id, date) ON CONFLICT REPLACE
        );
        """
    )

    # Leaves
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL,
            comment TEXT DEFAULT '',
            applied_date TEXT NOT NULL,
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        );
        """
    )

    # Payslips
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS payslips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            basic_salary REAL NOT NULL,
            adjusted_basic REAL DEFAULT 0,
            house_rent_allowance REAL DEFAULT 0,
            travel_allowance REAL DEFAULT 0,
            meal_allowance REAL DEFAULT 0,
            special_allowance REAL DEFAULT 0,
            allowances REAL NOT NULL,
            working_days INTEGER DEFAULT 0,
            present_days INTEGER DEFAULT 0,
            half_days INTEGER DEFAULT 0,
            paid_leave_days REAL DEFAULT 0,
            attendance_ratio REAL DEFAULT 1.0,
            pf_contribution REAL NOT NULL,
            esi_contribution REAL NOT NULL,
            tds REAL NOT NULL,
            other_deductions REAL DEFAULT 0,
            deductions REAL NOT NULL,
            net_salary REAL NOT NULL,
            generated_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            UNIQUE(employee_id, month, year) ON CONFLICT REPLACE,
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        );
        """
    )

    # Inquiries
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            date_submitted TEXT NOT NULL,
            status TEXT NOT NULL,
            response TEXT DEFAULT '',
            response_date TEXT,
            applied_date TEXT,
            priority TEXT DEFAULT 'Medium',
            category TEXT DEFAULT 'Payroll',
            assigned_to TEXT DEFAULT 'Unassigned',
            last_updated TEXT,
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        );
        """
    )

    # Audit Logs
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        """
    )

    # Compliance Filings
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS compliance_filings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            employees_covered INTEGER DEFAULT 0,
            total_amount REAL DEFAULT 0.0,
            generated_by TEXT NOT NULL,
            generated_date TEXT NOT NULL,
            last_modified TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            receipt_number TEXT DEFAULT NULL
        );
        """
    )

    # Employee Documents
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS employee_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            file_name TEXT NOT NULL,
            uploaded_date TEXT NOT NULL,
            file_size TEXT,
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        );
        """
    )

    # Employee Lifecycle
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS employee_lifecycle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_date TEXT NOT NULL,
            description TEXT NOT NULL,
            performed_by TEXT NOT NULL,
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        );
        """
    )

    # Payroll Profiles
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS payroll_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL UNIQUE,
            salary_structure TEXT DEFAULT 'Standard Class',
            basic_salary REAL NOT NULL,
            bank_account TEXT DEFAULT '',
            ifsc_code TEXT DEFAULT '',
            uan_number TEXT DEFAULT '',
            esi_number TEXT DEFAULT '',
            pf_number TEXT DEFAULT '',
            pan_number TEXT DEFAULT '',
            aadhaar_number TEXT DEFAULT '',
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        );
        """
    )

    # Attendance Profiles
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL UNIQUE,
            shift TEXT DEFAULT 'General',
            location TEXT DEFAULT 'Office',
            working_hours_per_day REAL DEFAULT 8.0,
            FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
        );
        """
    )

    con.commit()

    cur.execute("SELECT COUNT(*) AS c FROM users")
    users_count = cur.fetchone()["c"]
    if users_count and users_count > 0:
        con.close()
        return

    # -------------------------
    # Seed demo data
    # -------------------------
    admin_id = create_user(
        'Admin User', 'admin@example.com', generate_password_hash('admin123'), 'hr', con=con
    )

    departments = ['HR', 'IT', 'Finance', 'Marketing', 'Operations', 'Sales']
    designations = {
        'HR': ['HR Manager', 'HR Recruiter', 'HR Specialist'],
        'IT': ['Software Architect', 'Senior Developer', 'QA Engineer', 'DevOps Specialist'],
        'Finance': ['Financial Analyst', 'Accountant', 'Finance Lead'],
        'Marketing': ['SEO Expert', 'Content Writer', 'Marketing Manager'],
        'Operations': ['Operations Lead', 'Operations Associate'],
        'Sales': ['Sales Executive', 'Account Manager', 'Sales Director']
    }
    shifts = ['General', 'Morning', 'Evening', 'Night']
    locations = ['Office', 'WFH', 'Client Site']
    
    first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth',
                   'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen',
                   'Christopher', 'Nancy', 'Daniel', 'Lisa', 'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra',
                   'Donald', 'Ashley', 'Steven', 'Dorothy', 'Paul', 'Kimberly', 'Andrew', 'Emily', 'Joshua', 'Donna',
                   'Kenneth', 'Michelle', 'Kevin', 'Carol', 'Brian', 'Amanda', 'George', 'Melissa', 'Edward', 'Deborah']
    
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                  'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
                  'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
                  'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
                  'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell', 'Carter', 'Roberts']

    today = datetime.datetime.now().date()
    yesterday = today - datetime.timedelta(days=1)
    
    import random
    random.seed(42) # For reproducible random data
    
    # 1. Create John Doe (default employee) first
    j_user_id = create_user(
        'John Doe', 'employee@example.com', generate_password_hash('employee123'), 'employee', con=con
    )
    j_emp_id = create_employee_profile(
        j_user_id, 'IT', 'Software Developer', 5000.00, con=con
    )
    
    # List of all employee IDs to seed attendance for
    employees_to_seed = [(j_emp_id, j_user_id, 'IT', 'Software Developer', 5000.00)]
    
    # Create 49 more employees
    for i in range(49):
        fname = first_names[i % len(first_names)]
        lname = last_names[i % len(last_names)]
        name = f"{fname} {lname}"
        email = f"{fname.lower()}.{lname.lower()}@example.com"
        dept = random.choice(departments)
        desig = random.choice(designations[dept])
        salary = round(random.uniform(3000, 8000), 2)
        
        user_id = create_user(
            name, email, generate_password_hash('employee123'), 'employee', con=con
        )
        emp_id = create_employee_profile(
            user_id, dept, desig, salary, con=con
        )
        employees_to_seed.append((emp_id, user_id, dept, desig, salary))
        
    # 2. Seed 30 Days of Attendance
    for emp_id, user_id, dept, desig, salary in employees_to_seed:
        for day_offset in range(30):
            record_date = today - datetime.timedelta(days=day_offset)
            if record_date.weekday() >= 5: # Weekend
                if random.random() > 0.05: # 95% weekends are off
                    continue
            
            # Status randomizer
            roll = random.random()
            shift = random.choice(shifts)
            location = random.choice(locations)
            
            if roll < 0.75: # Present
                status = 'present'
                h_in = random.randint(8, 9)
                m_in = random.randint(0, 59)
                h_out = random.randint(17, 18)
                m_out = random.randint(0, 59)
                check_in = f"{h_in:02d}:{m_in:02d}"
                check_out = f"{h_out:02d}:{m_out:02d}"
                working_hours = round((h_out + m_out/60.0) - (h_in + m_in/60.0), 2)
                overtime_hours = max(0.0, round(working_hours - 8.0, 2))
                note = 'Regular day'
            elif roll < 0.85: # Late
                status = 'present'
                h_in = 10
                m_in = random.randint(0, 30)
                h_out = random.randint(17, 18)
                m_out = random.randint(0, 59)
                check_in = f"{h_in:02d}:{m_in:02d}"
                check_out = f"{h_out:02d}:{m_out:02d}"
                working_hours = round((h_out + m_out/60.0) - (h_in + m_in/60.0), 2)
                overtime_hours = 0.0
                note = 'Late arrival'
            elif roll < 0.90: # Half Day
                status = 'half_day'
                h_in = 9
                m_in = random.randint(0, 30)
                h_out = 13
                m_out = random.randint(0, 30)
                check_in = f"{h_in:02d}:{m_in:02d}"
                check_out = f"{h_out:02d}:{m_out:02d}"
                working_hours = round((h_out + m_out/60.0) - (h_in + m_in/60.0), 2)
                overtime_hours = 0.0
                note = 'Doctor appointment/Personal work'
            elif roll < 0.95: # WFH
                status = 'wfh'
                h_in = 9
                m_in = 0
                h_out = 18
                m_out = 0
                check_in = f"{h_in:02d}:{m_in:02d}"
                check_out = f"{h_out:02d}:{m_out:02d}"
                working_hours = 9.0
                overtime_hours = 1.0
                location = 'WFH'
                note = 'Working from home'
            else: # Absent
                status = 'absent'
                check_in = None
                check_out = None
                working_hours = 0.0
                overtime_hours = 0.0
                note = 'Absent without notice'
                
            cur.execute(
                """
                INSERT INTO attendance (
                    employee_id, date, status, note, check_in, check_out, working_hours, overtime_hours, location, shift
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (emp_id, str(record_date), status, note, check_in, check_out, working_hours, overtime_hours, location, shift),
            )
            
    # 3. Seed some leaves
    for emp_id, user_id, dept, desig, salary in employees_to_seed[:10]:
        start_leave = today + datetime.timedelta(days=random.randint(2, 10))
        end_leave = start_leave + datetime.timedelta(days=random.randint(1, 4))
        cur.execute(
            "INSERT INTO leaves (employee_id, start_date, end_date, leave_type, reason, status, comment, applied_date) VALUES (?,?,?,?,?,?,?,?)",
            (
                emp_id,
                str(start_leave),
                str(end_leave),
                random.choice(['annual', 'sick', 'casual']),
                'Personal work/Vacation',
                random.choice(['pending', 'approved', 'rejected']),
                '',
                str(today - datetime.timedelta(days=2)),
            ),
        )

    # 4. Seed payslips for all employees for last month
    last_month = datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)
    for emp_id, user_id, dept, desig, salary in employees_to_seed:
        basic_salary = salary
        house_rent_allowance = round(basic_salary * 0.15, 2)
        travel_allowance = round(basic_salary * 0.05, 2)
        meal_allowance = round(basic_salary * 0.03, 2)
        allowances = house_rent_allowance + travel_allowance + meal_allowance
        
        pf_contribution = round(basic_salary * 0.05, 2)
        esi_contribution = round(basic_salary * 0.02, 2)
        tds = round((basic_salary + allowances) * 0.05, 2)
        deductions = pf_contribution + esi_contribution + tds
        net_salary = basic_salary + allowances - deductions
        
        cur.execute(
            """
            INSERT INTO payslips (
                employee_id, month, year, basic_salary, adjusted_basic,
                house_rent_allowance, travel_allowance, meal_allowance, special_allowance,
                allowances, working_days, present_days, half_days, paid_leave_days, attendance_ratio,
                pf_contribution, esi_contribution, tds, other_deductions, deductions, net_salary, generated_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                emp_id, last_month.month, last_month.year, basic_salary, basic_salary,
                house_rent_allowance, travel_allowance, meal_allowance, 0.0,
                allowances, 22, 22, 0, 0.0, 1.0,
                pf_contribution, esi_contribution, tds, 0.0, deductions, net_salary, str(last_month.date()), 'approved'
            ),
        )

    # 5. Seed some inquiries
    categories = ['Payroll', 'Leaves', 'Tax', 'Benefits', 'Other']
    priorities = ['High', 'Medium', 'Low']
    for idx, (emp_id, user_id, dept, desig, salary) in enumerate(employees_to_seed[:5]):
        cat = categories[idx % len(categories)]
        pri = 'High' if idx == 0 else priorities[idx % len(priorities)]
        cur.execute(
            """
            INSERT INTO inquiries (
                employee_id, subject, message, date_submitted, status, response, response_date, applied_date, priority, category, assigned_to, last_updated
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                emp_id,
                'Question about PF contribution' if idx == 0 else f'Inquiry regarding {cat}',
                'Can you please clarify the PF contribution calculation for this month?' if idx == 0 else f'Hi HR, I have a detailed question regarding my {cat.lower()} settings.',
                str(yesterday),
                'pending',
                '',
                None,
                str(yesterday),
                pri,
                cat,
                'Unassigned',
                str(yesterday)
            ),
        )

    con.commit()
    con.close()


# -------------------------
# User functions
# -------------------------

def create_user(name, email, password, role, con=None):
    own_con = con is None
    con = con or _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO users (name, email, password, role, created_at) VALUES (?,?,?,?,?)",
            (name, email, password, role, str(datetime.datetime.now())),
        )
        con.commit()
        return cur.lastrowid
    finally:
        if own_con:
            con.close()


def find_user_by_email(email):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        return _row_to_dict(cur.fetchone())
    finally:
        con.close()


def find_user_by_id(user_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return _row_to_dict(cur.fetchone())
    finally:
        con.close()


# -------------------------
# Employee functions
# -------------------------

def create_employee_profile(user_id, department, designation, salary, con=None):
    own_con = con is None
    con = con or _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO employees (
                user_id, department, designation, address, phone, emergency_contact,
                date_of_birth, date_joined, basic_salary, status
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                user_id,
                department,
                designation,
                '',
                '',
                '',
                None,
                str(datetime.datetime.now().date()),
                float(salary),
                'active',
            ),
        )
        con.commit()
        return cur.lastrowid
    finally:
        if own_con:
            con.close()


def _employee_with_user_details(employee_row):
    # employee_row: sqlite Row from employees
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT id, name, email FROM users WHERE id = ?", (employee_row['user_id'],))
        user = cur.fetchone()
        if not user:
            return None
        base = dict(employee_row)
        base['name'] = user['name']
        base['email'] = user['email']
        return base
    finally:
        con.close()


def get_employee_by_user_id(user_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM employees WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            return None
        user = _row_to_dict(
            con.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
        )
        base = dict(row)
        base['name'] = user['name']
        base['email'] = user['email']
        return base
    finally:
        con.close()


def get_employee_by_id(employee_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
        row = cur.fetchone()
        if not row:
            return None
        user = _row_to_dict(
            con.execute("SELECT id, name, email FROM users WHERE id = ?", (row['user_id'],)).fetchone()
        )
        base = dict(row)
        base['name'] = user['name']
        base['email'] = user['email']
        return base
    finally:
        con.close()


def update_employee(user_id, name, email, address, phone, emergency_contact, date_of_birth, department, designation):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            """
            UPDATE employees
            SET address = ?, phone = ?, emergency_contact = ?, date_of_birth = ?, department = ?, designation = ?
            WHERE user_id = ?
            """,
            (address, phone, emergency_contact, str(date_of_birth) if date_of_birth else None, department, designation, user_id),
        )
        cur.execute(
            """
            UPDATE users
            SET name = ?, email = ?
            WHERE id = ?
            """,
            (name, email, user_id),
        )
        con.commit()
        return True
    finally:
        con.close()


def update_employee_hr(employee_id, name, department, designation, salary, status):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT user_id FROM employees WHERE id = ?", (employee_id,))
        row = cur.fetchone()
        if not row:
            return False
        user_id = row['user_id']

        cur.execute(
            """
            UPDATE employees
            SET department = ?, designation = ?, basic_salary = ?, status = ?
            WHERE id = ?
            """,
            (department, designation, float(salary), status, employee_id),
        )
        cur.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
        con.commit()
        return True
    finally:
        con.close()


def delete_employee_by_id(employee_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT user_id FROM employees WHERE id = ?", (employee_id,))
        row = cur.fetchone()
        if not row:
            return False
        user_id = row['user_id']

        cur.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        # user deleted via ON DELETE CASCADE in foreign key? FK is from employees->users, so delete employee won't delete user.
        # Keep behaviour closer to old code: delete user too.
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        con.commit()
        return True
    finally:
        con.close()


def get_all_employees():
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT e.*, u.name, u.email
            FROM employees e
            JOIN users u ON u.id = e.user_id
            """
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


def get_all_active_employees():
    return [e for e in get_all_employees() if e['status'] == 'active']


def get_total_employees():
    con = _get_con()
    try:
        return con.execute("SELECT COUNT(*) AS c FROM employees").fetchone()["c"]
    finally:
        con.close()


# -------------------------
# Attendance functions
# -------------------------

def mark_attendance(user_id, status, note):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM employees WHERE user_id = ?", (user_id,))
        emp = cur.fetchone()
        if not emp:
            raise ValueError("Employee profile not found")
        employee_id = emp['id']
        today = str(datetime.datetime.now().date())
        
        cur.execute(
            """
            INSERT INTO attendance (employee_id, date, status, note)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(employee_id, date, status) DO UPDATE SET note = excluded.note
            """,
            (employee_id, today, status, note)
        )
        con.commit()
        return cur.lastrowid
    finally:
        con.close()

def check_attendance_today(user_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM employees WHERE user_id = ?", (user_id,))
        emp = cur.fetchone()
        if not emp:
            return False
        employee_id = emp['id']
        today = str(datetime.datetime.now().date())
        cur.execute(
            "SELECT 1 FROM attendance WHERE employee_id = ? AND date = ?",
            (employee_id, today)
        )
        return cur.fetchone() is not None
    finally:
        con.close()

def get_attendance_history(user_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM employees WHERE user_id = ?", (user_id,))
        emp = cur.fetchone()
        if not emp:
            return []
        employee_id = emp['id']
        cur.execute(
            "SELECT * FROM attendance WHERE employee_id = ? ORDER BY date DESC",
            (employee_id,)
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        con.close()

def calculate_attendance_percentage(user_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM employees WHERE user_id = ?", (user_id,))
        emp = cur.fetchone()
        if not emp:
            return 0.0
        employee_id = emp['id']
        
        today = datetime.datetime.now().date()
        month_start = today.replace(day=1)
        
        # Calculate working days (excluding weekends)
        working_days = 0
        current_date = month_start
        while current_date <= today:
            if current_date.weekday() < 5:  # Monday to Friday
                working_days += 1
            current_date += datetime.timedelta(days=1)
        
        if working_days == 0:
            return 0.0
            
        cur.execute(
            """
            SELECT COUNT(*) AS c FROM attendance 
            WHERE employee_id = ? AND date >= ? AND date <= ? AND status IN ('present', 'wfh')
            """,
            (employee_id, str(month_start), str(today))
        )
        present_count = cur.fetchone()['c']
        
        cur.execute(
            """
            SELECT COUNT(*) AS c FROM attendance 
            WHERE employee_id = ? AND date >= ? AND date <= ? AND status = 'half_day'
            """,
            (employee_id, str(month_start), str(today))
        )
        half_count = cur.fetchone()['c']
        
        effective_present = present_count + (half_count * 0.5)
        return round((effective_present / working_days) * 100, 2)
    finally:
        con.close()

def get_filtered_attendance(date_filter, employee_filter, department_filter, status_filter=None, shift_filter=None):
    con = _get_con()
    try:
        cur = con.cursor()
        query = """
            SELECT a.*, u.name AS employee_name, e.department, e.designation, e.id AS employee_id
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            JOIN users u ON e.user_id = u.id
            WHERE 1=1
        """
        params = []
        if date_filter:
            query += " AND a.date = ?"
            params.append(date_filter)
        if employee_filter:
            query += " AND e.id = ?"
            params.append(employee_filter)
        if department_filter:
            query += " AND e.department = ?"
            params.append(department_filter)
        if status_filter:
            query += " AND a.status = ?"
            params.append(status_filter)
        if shift_filter:
            query += " AND a.shift = ?"
            params.append(shift_filter)
            
        query += " ORDER BY u.name ASC"
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        con.close()

def update_attendance_status(attendance_id, status):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE attendance SET status = ? WHERE id = ?",
            (status, int(attendance_id))
        )
        con.commit()
        return cur.rowcount > 0
    finally:
        con.close()

# Leave model functions
def apply_for_leave(user_id, start_date, end_date, leave_type, reason):
    logging.info(f"Database INSERT: Creating leave request for user_id={user_id}")
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM employees WHERE user_id = ?", (user_id,))
        emp = cur.fetchone()
        if not emp:
            logging.error(f"Database INSERT failed: Employee profile not found for user_id={user_id}")
            raise ValueError("Employee profile not found")
        employee_id = emp['id']
        
        cur.execute(
            """
            INSERT INTO leaves (employee_id, start_date, end_date, leave_type, reason, status, comment, applied_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (employee_id, str(start_date), str(end_date), leave_type, reason, 'pending', '', str(datetime.datetime.now().date()))
        )
        leave_id = cur.lastrowid
        con.commit()
        logging.info(f"Database INSERT success: Created leave_id={leave_id} for employee_id={employee_id}")
        log_activity(user_id, 'Leave Submitted', f"Submitted {leave_type} leave from {start_date} to {end_date} (ID: {leave_id})")
        return leave_id
    except Exception as e:
        logging.error(f"Database INSERT failed: {str(e)}")
        raise e
    finally:
        con.close()

def get_employee_leaves(user_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM employees WHERE user_id = ?", (user_id,))
        emp = cur.fetchone()
        if not emp:
            return []
        employee_id = emp['id']
        cur.execute(
            "SELECT * FROM leaves WHERE employee_id = ? ORDER BY applied_date DESC",
            (employee_id,)
        )
        leaves = []
        for row in cur.fetchall():
            res = dict(row)
            if isinstance(res['start_date'], str):
                res['start_date'] = datetime.datetime.strptime(res['start_date'], '%Y-%m-%d').date()
            if isinstance(res['end_date'], str):
                res['end_date'] = datetime.datetime.strptime(res['end_date'], '%Y-%m-%d').date()
            leaves.append(res)
        return leaves
    finally:
        con.close()

def get_leave_balance(user_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM employees WHERE user_id = ?", (user_id,))
        emp = cur.fetchone()
        if not emp:
            return {'annual': 20, 'sick': 10, 'casual': 5, 'unpaid': 'Unlimited'}
        employee_id = emp['id']
        
        # Calculate used leaves
        cur.execute(
            "SELECT leave_type, start_date, end_date FROM leaves WHERE employee_id = ? AND status = 'approved'",
            (employee_id,)
        )
        rows = cur.fetchall()
        
        used = {'annual': 0.0, 'sick': 0.0, 'casual': 0.0, 'unpaid': 0.0}
        for row in rows:
            start = datetime.datetime.strptime(row['start_date'], '%Y-%m-%d').date()
            end = datetime.datetime.strptime(row['end_date'], '%Y-%m-%d').date()
            days = (end - start).days + 1
            ltype = row['leave_type']
            if ltype in used:
                used[ltype] += days
                
        return {
            'annual': max(0, 20 - int(used['annual'])),
            'sick': max(0, 10 - int(used['sick'])),
            'casual': max(0, 5 - int(used['casual'])),
            'unpaid': 'Unlimited'
        }
    finally:
        con.close()

def get_pending_leaves(user_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM employees WHERE user_id = ?", (user_id,))
        emp = cur.fetchone()
        if not emp:
            return []
        employee_id = emp['id']
        cur.execute(
            "SELECT * FROM leaves WHERE employee_id = ? AND status = 'pending'",
            (employee_id,)
        )
        leaves = []
        for row in cur.fetchall():
            res = dict(row)
            if isinstance(res['start_date'], str):
                res['start_date'] = datetime.datetime.strptime(res['start_date'], '%Y-%m-%d').date()
            if isinstance(res['end_date'], str):
                res['end_date'] = datetime.datetime.strptime(res['end_date'], '%Y-%m-%d').date()
            leaves.append(res)
        return leaves
    finally:
        con.close()

def get_total_pending_leaves():
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM leaves WHERE status = 'pending'")
        return cur.fetchone()['c']
    finally:
        con.close()

def get_filtered_leave_requests(status_filter, department_filter):
    con = _get_con()
    try:
        cur = con.cursor()
        query = """
            SELECT l.*, u.name AS employee_name, e.department, e.designation
            FROM leaves l
            JOIN employees e ON l.employee_id = e.id
            JOIN users u ON e.user_id = u.id
            WHERE 1=1
        """
        params = []
        if status_filter:
            query += " AND l.status = ?"
            params.append(status_filter)
        if department_filter:
            query += " AND e.department = ?"
            params.append(department_filter)
            
        cur.execute(query, params)
        leaves = []
        for row in cur.fetchall():
            res = dict(row)
            if isinstance(res['start_date'], str):
                res['start_date'] = datetime.datetime.strptime(res['start_date'], '%Y-%m-%d').date()
            if isinstance(res['end_date'], str):
                res['end_date'] = datetime.datetime.strptime(res['end_date'], '%Y-%m-%d').date()
            leaves.append(res)
        return leaves
    finally:
        con.close()

def update_leave_request_status(leave_id, status, comment, admin_user_id=None):
    logging.info(f"Database UPDATE: Setting status={status} for leave_id={leave_id}")
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE leaves SET status = ?, comment = ? WHERE id = ?",
            (status, comment, int(leave_id))
        )
        con.commit()
        rowcount = cur.rowcount
        if rowcount > 0:
            logging.info(f"Database UPDATE success: Updated leave_id={leave_id} to status={status}")
            log_activity(admin_user_id, f"Leave {status.capitalize()}", f"Leave request ID {leave_id} has been {status}")
        else:
            logging.warning(f"Database UPDATE: No rows affected for leave_id={leave_id}")
        return rowcount > 0
    except Exception as e:
        logging.error(f"Database UPDATE failed: {str(e)}")
        raise e
    finally:
        con.close()

# -------------------------
# Audit logs & Leave Stats
# -------------------------
def log_activity(user_id, action, details):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO audit_logs (user_id, action, details, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, action, details, str(datetime.datetime.now()))
        )
        con.commit()
    except Exception as e:
        logging.error(f"Error logging activity: {str(e)}")
    finally:
        con.close()

def get_leave_stats():
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT status, COUNT(*) as c FROM leaves GROUP BY status")
        counts = {'pending': 0, 'approved': 0, 'rejected': 0, 'total': 0}
        for row in cur.fetchall():
            status = row['status'].lower()
            if status in counts:
                counts[status] = row['c']
                counts['total'] += row['c']
            
        today = str(datetime.datetime.now().date())
        cur.execute(
            "SELECT COUNT(DISTINCT employee_id) as c FROM leaves WHERE status = 'approved' AND start_date <= ? AND end_date >= ?",
            (today, today)
        )
        counts['on_leave_today'] = cur.fetchone()['c'] or 0
        return counts
    finally:
        con.close()

def get_leave_type_distribution():
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT leave_type, COUNT(*) as c FROM leaves GROUP BY leave_type")
        dist = {'annual': 0, 'sick': 0, 'casual': 0, 'unpaid': 0}
        for row in cur.fetchall():
            ltype = row['leave_type'].lower()
            if ltype in dist:
                dist[ltype] = row['c']
        return dist
    finally:
        con.close()

def get_department_leave_analysis():
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT e.department, l.leave_type, COUNT(*) as c
            FROM leaves l
            JOIN employees e ON l.employee_id = e.id
            GROUP BY e.department, l.leave_type
            """
        )
        analysis = {}
        for row in cur.fetchall():
            dept = row['department']
            ltype = row['leave_type'].lower()
            count = row['c']
            if dept not in analysis:
                analysis[dept] = {'annual': 0, 'sick': 0, 'casual': 0, 'unpaid': 0}
            if ltype in analysis[dept]:
                analysis[dept][ltype] = count
        return analysis
    finally:
        con.close()

def get_audit_logs(limit=20):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT a.*, u.name as user_name, u.role
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.timestamp DESC LIMIT ?
            """,
            (limit,)
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        con.close()

# Payroll model functions
def process_monthly_payroll(month, year, target_employee_id=None):
    con = _get_con()
    try:
        cur = con.cursor()
        if target_employee_id:
            cur.execute("DELETE FROM payslips WHERE month = ? AND year = ? AND employee_id = ?", (month, year, int(target_employee_id)))
        else:
            cur.execute("DELETE FROM payslips WHERE month = ? AND year = ?", (month, year))
        
        import calendar
        month_days = calendar.monthrange(year, month)[1]
        
        working_days = 0
        for day in range(1, month_days + 1):
            date = datetime.datetime(year, month, day).date()
            if date.weekday() < 5:
                working_days += 1
                
        query = """
            SELECT e.*, u.name, u.email
            FROM employees e
            JOIN users u ON u.id = e.user_id
            WHERE e.status = 'active'
        """
        params = []
        if target_employee_id:
            query += " AND e.id = ?"
            params.append(int(target_employee_id))
            
        cur.execute(query, params)
        employees = [dict(r) for r in cur.fetchall()]
        
        for employee in employees:
            employee_id = employee['id']
            basic_salary = employee['basic_salary']
            
            start_date_str = f"{year:04d}-{month:02d}-01"
            end_date_str = f"{year:04d}-{month:02d}-{month_days:02d}"
            
            cur.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM attendance
                WHERE employee_id = ? AND date >= ? AND date <= ?
                GROUP BY status
                """,
                (employee_id, start_date_str, end_date_str)
            )
            attendance_counts = {row['status']: row['count'] for row in cur.fetchall()}
            present_days = attendance_counts.get('present', 0)
            half_days = attendance_counts.get('half_day', 0)
            wfh_days = attendance_counts.get('wfh', 0)
            
            present_days += wfh_days
            
            cur.execute(
                """
                SELECT start_date, end_date, leave_type
                FROM leaves
                WHERE employee_id = ? AND status = 'approved'
                  AND start_date <= ? AND end_date >= ?
                """,
                (employee_id, end_date_str, start_date_str)
            )
            leaves = [dict(row) for row in cur.fetchall()]
            
            paid_leave_days = 0.0
            for leave in leaves:
                l_start = datetime.datetime.strptime(leave['start_date'], '%Y-%m-%d').date()
                l_end = datetime.datetime.strptime(leave['end_date'], '%Y-%m-%d').date()
                
                clip_start = max(l_start, datetime.date(year, month, 1))
                clip_end = min(l_end, datetime.date(year, month, month_days))
                
                leave_working_days = 0
                curr = clip_start
                while curr <= clip_end:
                    if curr.weekday() < 5:
                        leave_working_days += 1
                    curr += datetime.timedelta(days=1)
                    
                if leave['leave_type'] in ['annual', 'sick']:
                    paid_leave_days += leave_working_days
                elif leave['leave_type'] == 'casual':
                    paid_leave_days += leave_working_days * 0.5
                    
            effective_days = present_days + (half_days * 0.5) + paid_leave_days
            attendance_ratio = min(1.0, effective_days / working_days if working_days > 0 else 1.0)
            
            adjusted_basic = basic_salary * attendance_ratio
            
            house_rent_allowance = basic_salary * 0.15
            travel_allowance = basic_salary * 0.05
            meal_allowance = basic_salary * 0.03
            
            special_allowance = 0.0
            designation_lower = employee['designation'].lower()
            if any(role in designation_lower for role in ['manager', 'director', 'lead']):
                special_allowance = basic_salary * 0.1
            elif any(role in designation_lower for role in ['senior', 'specialist']):
                special_allowance = basic_salary * 0.05
                
            total_allowances = house_rent_allowance + (
                (travel_allowance + meal_allowance + special_allowance) * attendance_ratio
            )
            
            pf_contribution = adjusted_basic * 0.05
            esi_contribution = adjusted_basic * 0.02
            
            annual_salary = basic_salary * 12
            tds_rate = 0.0
            if annual_salary > 1000000:
                tds_rate = 0.3
            elif annual_salary > 500000:
                tds_rate = 0.2
            elif annual_salary > 250000:
                tds_rate = 0.1
            elif annual_salary > 50000:
                tds_rate = 0.05
                
            tds = (adjusted_basic + total_allowances) * tds_rate
            other_deductions = 0.0
            total_deductions = pf_contribution + esi_contribution + tds + other_deductions
            
            net_salary = adjusted_basic + total_allowances - total_deductions
            
            cur.execute(
                """
                INSERT INTO payslips (
                    employee_id, month, year, basic_salary, adjusted_basic,
                    house_rent_allowance, travel_allowance, meal_allowance, special_allowance,
                    allowances, working_days, present_days, half_days, paid_leave_days, attendance_ratio,
                    pf_contribution, esi_contribution, tds, other_deductions, deductions, net_salary, generated_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    employee_id, month, year, basic_salary, adjusted_basic,
                    house_rent_allowance, travel_allowance * attendance_ratio, meal_allowance * attendance_ratio, special_allowance * attendance_ratio,
                    total_allowances, working_days, present_days, half_days, paid_leave_days, attendance_ratio,
                    pf_contribution, esi_contribution, tds, other_deductions, total_deductions, net_salary, str(datetime.datetime.now()), 'pending'
                )
            )
            
        con.commit()
    finally:
        con.close()

def check_payroll_processed(month, year):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT 1 FROM payslips WHERE month = ? AND year = ?", (month, year))
        return cur.fetchone() is not None
    finally:
        con.close()

def get_employee_payslips(user_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM employees WHERE user_id = ?", (user_id,))
        emp = cur.fetchone()
        if not emp:
            return []
        employee_id = emp['id']
        cur.execute(
            "SELECT * FROM payslips WHERE employee_id = ? ORDER BY year DESC, month DESC",
            (employee_id,)
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        con.close()

def get_recent_payslip(user_id):
    payslips = get_employee_payslips(user_id)
    return payslips[0] if payslips else None

def get_filtered_payslips(month, year, employee_id):
    con = _get_con()
    try:
        cur = con.cursor()
        query = """
            SELECT p.*, u.name AS employee_name, e.department, e.designation
            FROM payslips p
            JOIN employees e ON p.employee_id = e.id
            JOIN users u ON e.user_id = u.id
            WHERE 1=1
        """
        params = []
        if month:
            query += " AND p.month = ?"
            params.append(int(month))
        if year:
            query += " AND p.year = ?"
            params.append(int(year))
        if employee_id:
            query += " AND p.employee_id = ?"
            params.append(int(employee_id))
            
        query += " ORDER BY p.year DESC, p.month DESC"
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        con.close()

def get_payslip_by_id(payslip_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT p.*, u.name AS employee_name, e.department, e.designation
            FROM payslips p
            JOIN employees e ON p.employee_id = e.id
            JOIN users u ON e.user_id = u.id
            WHERE p.id = ?
            """,
            (int(payslip_id),)
        )
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        if isinstance(res['generated_date'], str):
            try:
                res['generated_date'] = datetime.datetime.strptime(res['generated_date'], '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                try:
                    res['generated_date'] = datetime.datetime.strptime(res['generated_date'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    res['generated_date'] = datetime.datetime.now()
        return res
    finally:
        con.close()

def get_monthly_payroll_amount():
    con = _get_con()
    try:
        cur = con.cursor()
        current_month = datetime.datetime.now().month
        current_year = datetime.datetime.now().year
        cur.execute(
            "SELECT SUM(net_salary) AS total FROM payslips WHERE month = ? AND year = ?",
            (current_month, current_year)
        )
        res = cur.fetchone()
        return res['total'] if res and res['total'] else 0.0
    finally:
        con.close()

def update_payslip_status(payslip_id, status):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE payslips SET status = ? WHERE id = ?",
            (status, int(payslip_id))
        )
        con.commit()
        return cur.rowcount > 0
    finally:
        con.close()

def get_payslip_stats(month, year):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT status, COUNT(*) AS count, SUM(net_salary) AS total FROM payslips WHERE month = ? AND year = ? GROUP BY status",
            (month, year)
        )
        stats = {
            'total_employees': 0,
            'total_amount': 0.0,
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'processed_this_month': 0
        }
        for row in cur.fetchall():
            status = row['status'].lower()
            count = row['count']
            total = row['total'] or 0.0
            if status in stats:
                stats[status] = count
            stats['total_employees'] += count
            stats['total_amount'] += total
            stats['processed_this_month'] += count
        return stats
    finally:
        con.close()

def get_department_salary_distribution(month, year):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT e.department, SUM(p.net_salary) AS total
            FROM payslips p
            JOIN employees e ON p.employee_id = e.id
            WHERE p.month = ? AND p.year = ?
            GROUP BY e.department
            """,
            (month, year)
        )
        dist = {}
        for row in cur.fetchall():
            dist[row['department']] = row['total']
        return dist
    finally:
        con.close()

def get_payroll_monthly_trend():
    con = _get_con()
    try:
        cur = con.cursor()
        trend = []
        today = datetime.datetime.now()
        for i in range(5, -1, -1):
            d = today - datetime.timedelta(days=i*30)
            m = d.month
            y = d.year
            cur.execute(
                "SELECT SUM(net_salary) AS total, COUNT(*) AS count FROM payslips WHERE month = ? AND year = ?",
                (m, y)
            )
            row = cur.fetchone()
            total = row['total'] if row and row['total'] else 0.0
            count = row['count'] if row and row['count'] else 0
            from utils import get_month_name
            trend.append({
                'month_name': f"{get_month_name(m)[:3]} {y}",
                'total': total,
                'count': count
            })
        return trend
    finally:
        con.close()

# Inquiry model functions
def submit_inquiry(user_id, subject, message):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM employees WHERE user_id = ?", (user_id,))
        emp = cur.fetchone()
        if not emp:
            raise ValueError("Employee profile not found")
        employee_id = emp['id']
        
        cur.execute(
            """
            INSERT INTO inquiries (employee_id, subject, message, date_submitted, status, response, response_date, applied_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (employee_id, subject, message, str(datetime.datetime.now()), 'pending', '', None, str(datetime.datetime.now().date()))
        )
        con.commit()
        return cur.lastrowid
    finally:
        con.close()

# -------------------------
# Inquiry Analytics Stats
# -------------------------
def get_inquiry_stats():
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT status, COUNT(*) AS count FROM inquiries GROUP BY status")
        stats = {
            'total': 0,
            'pending': 0,
            'in_progress': 0,
            'resolved': 0,
            'high_priority': 0
        }
        for row in cur.fetchall():
            status = row['status'].lower().replace(' ', '_')
            count = row['count']
            if status in stats:
                stats[status] = count
            stats['total'] += count
            
        cur.execute("SELECT COUNT(*) AS count FROM inquiries WHERE priority = 'High'")
        stats['high_priority'] = cur.fetchone()['count'] or 0
        return stats
    finally:
        con.close()

def get_inquiry_category_distribution():
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT category, COUNT(*) AS count FROM inquiries GROUP BY category")
        dist = {
            'Payroll': 0,
            'Leaves': 0,
            'Tax': 0,
            'Benefits': 0,
            'Other': 0
        }
        for row in cur.fetchall():
            cat = row['category']
            if cat in dist:
                dist[cat] = row['count']
        return dist
    finally:
        con.close()

def get_employee_inquiries(user_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM employees WHERE user_id = ?", (user_id,))
        emp = cur.fetchone()
        if not emp:
            return []
        employee_id = emp['id']
        cur.execute(
            "SELECT * FROM inquiries WHERE employee_id = ? ORDER BY date_submitted DESC",
            (employee_id,)
        )
        inquiries = []
        for row in cur.fetchall():
            res = dict(row)
            if isinstance(res['date_submitted'], str):
                for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                    try:
                        res['date_submitted'] = datetime.datetime.strptime(res['date_submitted'], fmt)
                        break
                    except ValueError:
                        pass
            if isinstance(res['response_date'], str):
                for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                    try:
                        res['response_date'] = datetime.datetime.strptime(res['response_date'], fmt)
                        break
                    except ValueError:
                        pass
            inquiries.append(res)
        return inquiries
    finally:
        con.close()

def get_filtered_inquiries(status_filter):
    con = _get_con()
    try:
        cur = con.cursor()
        query = """
            SELECT i.*, u.name AS employee_name, u.email AS employee_email, e.department
            FROM inquiries i
            JOIN employees e ON i.employee_id = e.id
            JOIN users u ON e.user_id = u.id
            WHERE 1=1
        """
        params = []
        if status_filter:
            query += " AND i.status = ?"
            params.append(status_filter)
            
        query += " ORDER BY i.date_submitted DESC"
        cur.execute(query, params)
        inquiries = []
        for row in cur.fetchall():
            res = dict(row)
            if isinstance(res['date_submitted'], str):
                for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                    try:
                        res['date_submitted'] = datetime.datetime.strptime(res['date_submitted'], fmt)
                        break
                    except ValueError:
                        pass
            if isinstance(res['response_date'], str):
                for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                    try:
                        res['response_date'] = datetime.datetime.strptime(res['response_date'], fmt)
                        break
                    except ValueError:
                        pass
            inquiries.append(res)
        return inquiries
    finally:
        con.close()

def update_inquiry_response(inquiry_id, response):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            """
            UPDATE inquiries 
            SET response = ?, status = 'responded', response_date = ?
            WHERE id = ?
            """,
            (response, str(datetime.datetime.now()), int(inquiry_id))
        )
        con.commit()
        return cur.rowcount > 0
    finally:
        con.close()

# Reports functions
# Reports functions
def generate_compliance_report(month, year, report_type):
    con = _get_con()
    try:
        cur = con.cursor()
        report_data = {
            'month': month,
            'year': year,
            'type': report_type,
            'employees': []
        }
        
        # Get filing status for this report
        cur.execute(
            "SELECT status, receipt_number FROM compliance_filings WHERE report_type = ? AND month = ? AND year = ?",
            (report_type, int(month), int(year))
        )
        filing = cur.fetchone()
        filing_status = filing['status'] if filing else 'Pending'
        receipt_number = filing['receipt_number'] if filing else None
        
        report_data['filing_status'] = filing_status
        report_data['receipt_number'] = receipt_number
        
        cur.execute(
            """
            SELECT p.*, u.name AS employee_name, e.id AS emp_id,
                   e.uan_number, e.esi_number, e.pan_number, e.aadhaar_number, e.state,
                   e.pf_status, e.esi_status, e.pt_status
            FROM payslips p
            JOIN employees e ON p.employee_id = e.id
            JOIN users u ON e.user_id = u.id
            WHERE p.month = ? AND p.year = ?
            """,
            (int(month), int(year))
        )
        payslips = [dict(row) for row in cur.fetchall()]
        
        for payslip in payslips:
            gross_salary = payslip['basic_salary'] + payslip['allowances']
            employee_data = {
                'id': payslip['emp_id'],
                'name': payslip['employee_name'],
                'basic_salary': payslip['basic_salary'],
                'gross_salary': gross_salary,
                'uan_number': payslip['uan_number'] or 'N/A',
                'esi_number': payslip['esi_number'] or 'N/A',
                'pan_number': payslip['pan_number'] or 'N/A',
                'aadhaar_number': payslip['aadhaar_number'] or 'N/A',
                'state': payslip['state'] or 'Maharashtra',
                'filing_status': filing_status
            }
            
            if report_type == 'pf':
                employee_data['pf_wages'] = payslip['basic_salary']
                employee_data['employee_contribution'] = payslip['pf_contribution']
                employee_data['employer_contribution'] = payslip['pf_contribution'] # Employer matches 5%
                employee_data['total_pf'] = payslip['pf_contribution'] * 2
                employee_data['contribution'] = payslip['pf_contribution']
            elif report_type == 'esi':
                employee_data['employee_contribution'] = payslip['esi_contribution']
                # Employer ESI contribution: 3% of gross salary
                employee_data['employer_contribution'] = round(gross_salary * 0.03, 2)
                employee_data['total_esi'] = round(employee_data['employee_contribution'] + employee_data['employer_contribution'], 2)
                employee_data['contribution'] = payslip['esi_contribution']
            elif report_type == 'tds':
                employee_data['taxable_income'] = gross_salary
                employee_data['tds_deducted'] = payslip['tds']
                # Financial year: April to March
                m = int(month)
                y = int(year)
                if m >= 4:
                    employee_data['financial_year'] = f"{y}-{y+1}"
                else:
                    employee_data['financial_year'] = f"{y-1}-{y}"
                employee_data['contribution'] = payslip['tds']
            elif report_type == 'pt':
                pt_amount = 2.00 if gross_salary > 5000 else 1.50
                employee_data['pt_amount'] = pt_amount
                employee_data['contribution'] = pt_amount
            else:
                employee_data['contribution'] = 0.0
                
            report_data['employees'].append(employee_data)
            
        report_data['total_contribution'] = sum(emp['contribution'] for emp in report_data['employees'])
        
        # Calculate matching totals based on report type
        if report_type == 'pf':
            report_data['total_pf_wages'] = sum(emp['pf_wages'] for emp in report_data['employees'])
            report_data['total_employee_contribution'] = sum(emp['employee_contribution'] for emp in report_data['employees'])
            report_data['total_employer_contribution'] = sum(emp['employer_contribution'] for emp in report_data['employees'])
            report_data['total_pf_amount'] = sum(emp['total_pf'] for emp in report_data['employees'])
        elif report_type == 'esi':
            report_data['total_gross_salary'] = sum(emp['gross_salary'] for emp in report_data['employees'])
            report_data['total_employee_contribution'] = sum(emp['employee_contribution'] for emp in report_data['employees'])
            report_data['total_employer_contribution'] = sum(emp['employer_contribution'] for emp in report_data['employees'])
            report_data['total_esi'] = sum(emp['total_esi'] for emp in report_data['employees'])
        elif report_type == 'tds':
            report_data['total_taxable_income'] = sum(emp['taxable_income'] for emp in report_data['employees'])
            report_data['total_tds_deducted'] = sum(emp['tds_deducted'] for emp in report_data['employees'])
        elif report_type == 'pt':
            report_data['total_gross_salary'] = sum(emp['gross_salary'] for emp in report_data['employees'])
            report_data['total_pt_amount'] = sum(emp['pt_amount'] for emp in report_data['employees'])
            
        report_data['total_employees'] = len(report_data['employees'])
        
        return report_data
    finally:
        con.close()

def get_compliance_dashboard_stats(month, year):
    con = _get_con()
    try:
        cur = con.cursor()
        
        # 1. Total Employees
        cur.execute("SELECT COUNT(*) FROM employees")
        total_employees = cur.fetchone()[0] or 0
        
        # 2. PF Registered
        cur.execute("SELECT COUNT(*) FROM employees WHERE uan_number IS NOT NULL AND uan_number != '' AND pf_status = 'Active'")
        pf_registered = cur.fetchone()[0] or 0
        
        # 3. ESI Registered
        cur.execute("SELECT COUNT(*) FROM employees WHERE esi_number IS NOT NULL AND esi_number != '' AND esi_status = 'Active'")
        esi_registered = cur.fetchone()[0] or 0
        
        # 4. PT Registered
        cur.execute("SELECT COUNT(*) FROM employees WHERE pt_status = 'Active'")
        pt_registered = cur.fetchone()[0] or 0
        
        # 5. TDS Deductions This Month
        cur.execute("SELECT SUM(tds) FROM payslips WHERE month = ? AND year = ?", (int(month), int(year)))
        tds_deductions = cur.fetchone()[0] or 0.0
        
        # 6. Filings for this month
        cur.execute("SELECT report_type, status FROM compliance_filings WHERE month = ? AND year = ?", (int(month), int(year)))
        filings = {row['report_type']: row['status'] for row in cur.fetchall()}
        
        filed_count = sum(1 for status in filings.values() if status == 'Filed')
        pending_filings = 4 - filed_count
        
        # 7. Compliance Score calculation
        cur.execute(
            """
            SELECT COUNT(*) FROM employees 
            WHERE pan_number IS NOT NULL AND pan_number != ''
              AND uan_number IS NOT NULL AND uan_number != ''
              AND esi_number IS NOT NULL AND esi_number != ''
              AND aadhaar_number IS NOT NULL AND aadhaar_number != ''
            """
        )
        complete_docs = cur.fetchone()[0] or 0
        doc_ratio = (complete_docs / total_employees * 100) if total_employees > 0 else 100
        filing_ratio = (filed_count / 4 * 100)
        
        compliance_score = round(0.7 * filing_ratio + 0.3 * doc_ratio)
        
        # 8. Upcoming deadlines (based on reported month)
        import calendar
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        next_month_name = calendar.month_name[next_month]
        
        deadlines = [
            {'type': 'PF Filing', 'due_date': f"{next_month_name} 15, {next_year}", 'status': filings.get('pf', 'Pending')},
            {'type': 'ESI Filing', 'due_date': f"{next_month_name} 15, {next_year}", 'status': filings.get('esi', 'Pending')},
            {'type': 'TDS Filing', 'due_date': f"{next_month_name} 07, {next_year}", 'status': filings.get('tds', 'Pending')},
            {'type': 'PT Filing', 'due_date': f"{next_month_name} 20, {next_year}", 'status': filings.get('pt', 'Pending')},
        ]
        
        return {
            'total_employees': total_employees,
            'pf_registered': pf_registered,
            'esi_registered': esi_registered,
            'pt_registered': pt_registered,
            'tds_deductions': tds_deductions,
            'compliance_score': compliance_score,
            'pending_filings': pending_filings,
            'deadlines': deadlines
        }
    finally:
        con.close()

def get_compliance_alerts():
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT e.id, u.name, e.department, e.designation,
                   e.pan_number, e.uan_number, e.esi_number, e.aadhaar_number
            FROM employees e
            JOIN users u ON e.user_id = u.id
            """
        )
        employees = cur.fetchall()
        alerts = []
        for emp in employees:
            missing_items = []
            if not emp['pan_number'] or emp['pan_number'] == '':
                missing_items.append('PAN')
            if not emp['uan_number'] or emp['uan_number'] == '':
                missing_items.append('UAN')
            if not emp['esi_number'] or emp['esi_number'] == '':
                missing_items.append('ESI Number')
            if not emp['aadhaar_number'] or emp['aadhaar_number'] == '':
                missing_items.append('Aadhaar')
                
            if missing_items:
                alerts.append({
                    'id': emp['id'],
                    'name': emp['name'],
                    'department': emp['department'],
                    'designation': emp['designation'],
                    'missing': missing_items
                })
        return alerts
    finally:
        con.close()

def get_compliance_filings():
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT * FROM compliance_filings
            ORDER BY year DESC, month DESC, report_type ASC
            """
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        con.close()

def mark_compliance_filed(report_type, month, year, generated_by):
    con = _get_con()
    try:
        cur = con.cursor()
        # Calculate summary values from payslips
        cur.execute(
            """
            SELECT COUNT(p.id) AS count, 
                   SUM(
                       CASE 
                           WHEN ? = 'pf' THEN p.pf_contribution
                           WHEN ? = 'esi' THEN p.esi_contribution
                           WHEN ? = 'tds' THEN p.tds
                           ELSE 0.0
                       END
                   ) AS amount
            FROM payslips p
            WHERE p.month = ? AND p.year = ?
            """,
            (report_type, report_type, report_type, int(month), int(year))
        )
        summary = cur.fetchone()
        count = summary['count'] or 0
        amount = summary['amount'] or 0.0
        
        # If PT is selected, amount is based on employees gross salary PT amount
        if report_type == 'pt':
            cur.execute(
                """
                SELECT COUNT(p.id) AS count,
                       SUM(CASE WHEN (p.basic_salary + p.allowances) > 5000 THEN 2.00 ELSE 1.50 END) AS amount
                FROM payslips p
                WHERE p.month = ? AND p.year = ?
                """,
                (int(month), int(year))
            )
            pt_summary = cur.fetchone()
            count = pt_summary['count'] or 0
            amount = pt_summary['amount'] or 0.0

        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        import random as rand
        receipt = f"ACK-{report_type.upper()}-{year}{month:02d}-{rand.randint(1000, 9999)}"
        
        cur.execute(
            "SELECT id FROM compliance_filings WHERE report_type = ? AND month = ? AND year = ?",
            (report_type, int(month), int(year))
        )
        existing = cur.fetchone()
        if existing:
            cur.execute(
                """
                UPDATE compliance_filings
                SET employees_covered = ?, total_amount = ?, generated_by = ?, last_modified = ?, status = 'Filed', receipt_number = ?
                WHERE id = ?
                """,
                (count, amount, generated_by, now_str, receipt, existing['id'])
            )
        else:
            cur.execute(
                """
                INSERT INTO compliance_filings (report_type, month, year, employees_covered, total_amount, generated_by, generated_date, last_modified, status, receipt_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Filed', ?)
                """,
                (report_type, int(month), int(year), count, amount, generated_by, now_str, now_str, receipt)
            )
        con.commit()
        return True
    finally:
        con.close()

def get_recent_activities():
    con = _get_con()
    try:
        cur = con.cursor()
        activities = []
        
        # Recent leaves
        cur.execute(
            """
            SELECT l.applied_date, l.leave_type, u.name AS employee_name
            FROM leaves l
            JOIN employees e ON l.employee_id = e.id
            JOIN users u ON e.user_id = u.id
            ORDER BY l.applied_date DESC LIMIT 5
            """
        )
        for row in cur.fetchall():
            activities.append({
                'type': 'leave',
                'employee_name': row['employee_name'],
                'date': row['applied_date'],
                'description': f"Applied for {row['leave_type']} leave"
            })
            
        # Recent attendance
        cur.execute(
            """
            SELECT a.date, a.status, u.name AS employee_name
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            JOIN users u ON e.user_id = u.id
            ORDER BY a.date DESC LIMIT 5
            """
        )
        for row in cur.fetchall():
            activities.append({
                'type': 'attendance',
                'employee_name': row['employee_name'],
                'date': row['date'],
                'description': f"Marked as {row['status']}"
            })
            
        # Recent inquiries
        cur.execute(
            """
            SELECT i.date_submitted, i.subject, u.name AS employee_name
            FROM inquiries i
            JOIN employees e ON i.employee_id = e.id
            JOIN users u ON e.user_id = u.id
            ORDER BY i.date_submitted DESC LIMIT 5
            """
        )
        for row in cur.fetchall():
            dt = row['date_submitted']
            if isinstance(dt, str):
                for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                    try:
                        dt = datetime.datetime.strptime(dt, fmt).date()
                        break
                    except ValueError:
                        pass
                else:
                    dt = datetime.datetime.now().date()
            activities.append({
                'type': 'inquiry',
                'employee_name': row['employee_name'],
                'date': str(dt),
                'description': f"Submitted inquiry: {row['subject']}"
            })
            
        # Sort activities
        activities = sorted(activities, key=lambda x: x['date'], reverse=True)
        return activities[:10]
    finally:
        con.close()

# Advanced Employee Management System Helpers
def get_employee_dashboard_stats():
    con = _get_con()
    try:
        cur = con.cursor()
        
        # Total
        cur.execute("SELECT COUNT(*) FROM employees")
        total = cur.fetchone()[0] or 0
        
        # Active
        cur.execute("SELECT COUNT(*) FROM employees WHERE status = 'active'")
        active = cur.fetchone()[0] or 0
        
        # Inactive
        cur.execute("SELECT COUNT(*) FROM employees WHERE status = 'inactive'")
        inactive = cur.fetchone()[0] or 0
        
        # New hires this month (joining date in current month & year)
        today = datetime.date.today()
        first_of_month = f"{today.year}-{today.month:02d}-01"
        cur.execute("SELECT COUNT(*) FROM employees WHERE date_joined >= ? AND status = 'active'", (first_of_month,))
        new_hires = cur.fetchone()[0] or 0
        
        # Employees on leave today
        today_str = today.strftime('%Y-%m-%d')
        cur.execute(
            """
            SELECT COUNT(DISTINCT employee_id) FROM leaves 
            WHERE status = 'approved' AND start_date <= ? AND end_date >= ?
            """,
            (today_str, today_str)
        )
        on_leave = cur.fetchone()[0] or 0
        
        # Probation
        cur.execute("SELECT COUNT(*) FROM employees WHERE probation_status = 'Probation'")
        probation = cur.fetchone()[0] or 0
        
        # Contract
        cur.execute("SELECT COUNT(*) FROM employees WHERE employee_type = 'Contract'")
        contract = cur.fetchone()[0] or 0
        
        # Resigned
        cur.execute("SELECT COUNT(*) FROM employees WHERE status = 'terminated' OR status = 'resigned'")
        resigned = cur.fetchone()[0] or 0
        
        return {
            'total': total,
            'active': active,
            'inactive': inactive,
            'new_hires': new_hires,
            'on_leave': on_leave,
            'probation': probation,
            'contract': contract,
            'resigned': resigned
        }
    finally:
        con.close()

def get_employee_documents(employee_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM employee_documents WHERE employee_id = ? ORDER BY id DESC", (employee_id,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        con.close()

def add_employee_document(employee_id, document_type, file_name, file_size):
    con = _get_con()
    try:
        cur = con.cursor()
        now_str = datetime.datetime.now().strftime('%Y-%m-%d')
        cur.execute(
            """
            INSERT INTO employee_documents (employee_id, document_type, file_name, uploaded_date, file_size)
            VALUES (?, ?, ?, ?, ?)
            """,
            (employee_id, document_type, file_name, now_str, file_size)
        )
        con.commit()
        return True
    finally:
        con.close()

def delete_employee_document(document_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM employee_documents WHERE id = ?", (document_id,))
        con.commit()
        return True
    finally:
        con.close()

def get_employee_lifecycle(employee_id):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM employee_lifecycle WHERE employee_id = ? ORDER BY event_date DESC, id DESC", (employee_id,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        con.close()

def add_lifecycle_event(employee_id, event_type, description, performed_by):
    con = _get_con()
    try:
        cur = con.cursor()
        now_str = datetime.datetime.now().strftime('%Y-%m-%d')
        cur.execute(
            """
            INSERT INTO employee_lifecycle (employee_id, event_type, event_date, description, performed_by)
            VALUES (?, ?, ?, ?, ?)
            """,
            (employee_id, event_type, now_str, description, performed_by)
        )
        con.commit()
        return True
    finally:
        con.close()

def update_employee_profile_hr(employee_id, name, gender, marital_status, blood_group, nationality,
                               phone, alternate_phone, address, emergency_contact,
                               employee_code, department, designation, branch, reporting_manager,
                               employee_type, probation_status, salary, salary_structure,
                               bank_account, ifsc_code, pf_number, uan_number, esi_number, tax_info, status):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("SELECT user_id FROM employees WHERE id = ?", (employee_id,))
        row = cur.fetchone()
        if not row:
            return False
        user_id = row['user_id']
        
        cur.execute(
            """
            UPDATE employees
            SET gender = ?, marital_status = ?, blood_group = ?, nationality = ?,
                phone = ?, alternate_phone = ?, address = ?, emergency_contact = ?,
                employee_code = ?, department = ?, designation = ?, branch = ?, reporting_manager = ?,
                employee_type = ?, probation_status = ?, basic_salary = ?, salary_structure = ?,
                bank_account = ?, ifsc_code = ?, pf_number = ?, uan_number = ?, esi_number = ?, 
                tax_info = ?, status = ?
            WHERE id = ?
            """,
            (gender, marital_status, blood_group, nationality,
             phone, alternate_phone, address, emergency_contact,
             employee_code, department, designation, branch, reporting_manager,
             employee_type, probation_status, float(salary), salary_structure,
             bank_account, ifsc_code, pf_number, uan_number, esi_number, tax_info, status, employee_id)
        )
        
        cur.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
        con.commit()
        return True
    finally:
        con.close()

def generate_next_employee_code():
    con = _get_con()
    try:
        cur = con.cursor()
        year = datetime.datetime.now().year
        cur.execute("SELECT employee_code FROM employees WHERE employee_code LIKE ?", (f"EMP-{year}-%",))
        codes = [row[0] for row in cur.fetchall() if row[0]]
        
        max_num = 0
        for code in codes:
            try:
                parts = code.split('-')
                if len(parts) == 3:
                    num = int(parts[2])
                    if num > max_num:
                        max_num = num
            except:
                pass
                
        next_num = max_num + 1
        return f"EMP-{year}-{next_num:04d}"
    finally:
        con.close()

def generate_username_from_name(name):
    parts = [p.lower().strip() for p in name.split(' ') if p.strip()]
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    elif len(parts) == 1:
        return parts[0]
    return "employee"

def update_employee_self(user_id, name, gender, date_of_birth, marital_status, blood_group, nationality, phone, alternate_phone, personal_email, address, emergency_contact_name, emergency_contact_phone, aadhaar_number, pan_number):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            """
            UPDATE employees
            SET gender = ?, date_of_birth = ?, marital_status = ?, blood_group = ?, nationality = ?,
                phone = ?, alternate_phone = ?, personal_email = ?, address = ?, 
                emergency_contact_name = ?, emergency_contact_phone = ?,
                aadhaar_number = ?, pan_number = ?
            WHERE user_id = ?
            """,
            (gender, str(date_of_birth) if date_of_birth else None, marital_status, blood_group, nationality,
             phone, alternate_phone, personal_email, address, emergency_contact_name, emergency_contact_phone,
             aadhaar_number, pan_number, user_id)
        )
        cur.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
        con.commit()
        return True
    finally:
        con.close()

def update_employee_avatar(user_id, avatar_url):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("UPDATE employees SET avatar_url = ? WHERE user_id = ?", (avatar_url, user_id))
        con.commit()
        return True
    finally:
        con.close()

def get_user_audit_logs(user_id, limit=20):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT a.*, u.name as user_name, u.role
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE a.user_id = ?
            ORDER BY a.timestamp DESC LIMIT ?
            """,
            (user_id, limit)
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        con.close()

def toggle_user_2fa(user_id, enabled):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("UPDATE users SET two_factor_enabled = ? WHERE id = ?", (1 if enabled else 0, user_id))
        con.commit()
        return True
    finally:
        con.close()

def replace_employee_document(employee_id, document_type, file_name, file_size):
    con = _get_con()
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM employee_documents WHERE employee_id = ? AND document_type = ?", (employee_id, document_type))
        now_str = datetime.datetime.now().strftime('%Y-%m-%d')
        cur.execute(
            """
            INSERT INTO employee_documents (employee_id, document_type, file_name, uploaded_date, file_size)
            VALUES (?, ?, ?, ?, ?)
            """,
            (employee_id, document_type, file_name, now_str, file_size)
        )
        con.commit()
        return True
    finally:
        con.close()

