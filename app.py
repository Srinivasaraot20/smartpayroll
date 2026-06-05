import os
import logging
from datetime import timedelta
import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect  # This is still valid
# Other necessary imports
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

from models import *
from models import _get_con
from forms import *
from utils import *

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Get Flask app from main.py
from main import app

# Make common functions available in templates
app.jinja_env.globals.update(
    get_month_name=get_month_name,
    calculate_days_in_month=calculate_days_in_month,
    calculate_working_days=calculate_working_days,
    format_currency=format_currency,
    check_attendance_today=check_attendance_today,
    get_leave_balance=get_leave_balance
)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize in-memory database
init_db()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'hr':
            return redirect(url_for('hr_dashboard'))
        else:
            return redirect(url_for('employee_dashboard'))
    return redirect(url_for('login'))

@app.before_request
def check_forced_password_change():
    if 'user_id' in session:
        if request.endpoint and request.endpoint in ['change_password', 'logout', 'static']:
            return
        user_id = session['user_id']
        con = _get_con()
        try:
            cur = con.cursor()
            cur.execute("SELECT force_password_change FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            if row and row['force_password_change'] == 1:
                flash('You are required to change your temporary password before proceeding.', 'warning')
                return redirect(url_for('change_password'))
        finally:
            con.close()

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        flash('Please login first', 'danger')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('change_password.html')
            
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('change_password.html')
            
        password_hash = generate_password_hash(new_password)
        user_id = session['user_id']
        con = _get_con()
        try:
            cur = con.cursor()
            cur.execute(
                "UPDATE users SET password = ?, force_password_change = 0 WHERE id = ?",
                (password_hash, user_id)
            )
            con.commit()
            flash('Password changed successfully! You now have full access.', 'success')
            
            role = session.get('role')
            if role == 'hr':
                return redirect(url_for('hr_dashboard'))
            else:
                return redirect(url_for('employee_dashboard'))
        except Exception as e:
            flash(f'Failed to change password: {str(e)}', 'danger')
        finally:
            con.close()
            
    return render_template('change_password.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        user = find_user_by_email(email)
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = user['role']
            session['email'] = user['email']
            session.permanent = True
            
            flash('Login successful!', 'success')
            if user['role'] == 'hr':
                return redirect(url_for('hr_dashboard'))
            else:
                return redirect(url_for('employee_dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        role = form.role.data
        
        if find_user_by_email(email):
            flash('Email already registered', 'danger')
            return render_template('register.html', form=form)
        
        password_hash = generate_password_hash(password)
        user_id = create_user(name, email, password_hash, role)
        
        if role == 'employee':
            create_employee_profile(user_id, 'Engineering', 'Staff', 3000.0)
            
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Employee routes
@app.route('/employee/dashboard')
@employee_required
def employee_dashboard():
    user_id = session.get('user_id')
    employee = get_employee_by_user_id(user_id)
    
    # Get attendance percentage
    attendance_percentage = calculate_attendance_percentage(user_id)
    
    # Get recent payslip
    recent_payslip = get_recent_payslip(user_id)
    
    # Get pending leave requests
    pending_leaves = get_pending_leaves(user_id)
    
    return render_template('employee/dashboard.html', 
                           employee=employee,
                           attendance_percentage=attendance_percentage,
                           recent_payslip=recent_payslip,
                           pending_leaves=pending_leaves)

@app.route('/employee/profile', methods=['GET', 'POST'])
@employee_required
def employee_profile():
    from werkzeug.utils import secure_filename
    user_id = session.get('user_id')
    employee = get_employee_by_user_id(user_id)
    if not employee:
        flash('Employee profile not found.', 'danger')
        return redirect(url_for('employee_dashboard'))
    
    # Process actions on POST
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            name = request.form.get('name')
            gender = request.form.get('gender', 'Male')
            dob_str = request.form.get('date_of_birth')
            marital_status = request.form.get('marital_status', 'Single')
            blood_group = request.form.get('blood_group', 'O+')
            nationality = request.form.get('nationality', 'Indian')
            
            personal_email = request.form.get('personal_email')
            phone = request.form.get('phone')
            alternate_phone = request.form.get('alternate_phone')
            address = request.form.get('address')
            emergency_contact_name = request.form.get('emergency_contact_name')
            emergency_contact_phone = request.form.get('emergency_contact_phone')
            
            aadhaar_number = request.form.get('aadhaar_number')
            pan_number = request.form.get('pan_number')
            
            # Simple date parsing
            dob = None
            if dob_str:
                try:
                    dob = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            # Update
            update_employee_self(
                user_id, name, gender, dob, marital_status, blood_group, nationality,
                phone, alternate_phone, personal_email, address,
                emergency_contact_name, emergency_contact_phone,
                aadhaar_number, pan_number
            )
            
            session['name'] = name
            log_activity(user_id, 'Profile Update', 'Updated self profile details')
            flash('Profile updated successfully', 'success')
            return redirect(url_for('employee_profile'))
            
        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not current_password or not new_password or not confirm_password:
                flash('All password fields are required.', 'danger')
                return redirect(url_for('employee_profile', tab='security'))
                
            if new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('employee_profile', tab='security'))
                
            if len(new_password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return redirect(url_for('employee_profile', tab='security'))
                
            con = _get_con()
            try:
                cur = con.cursor()
                cur.execute("SELECT password FROM users WHERE id = ?", (user_id,))
                user_row = cur.fetchone()
                if user_row and check_password_hash(user_row['password'], current_password):
                    password_hash = generate_password_hash(new_password)
                    cur.execute("UPDATE users SET password = ?, force_password_change = 0 WHERE id = ?", (password_hash, user_id))
                    con.commit()
                    log_activity(user_id, 'Password Change', 'Changed password from profile center')
                    flash('Password changed successfully.', 'success')
                else:
                    flash('Incorrect current password.', 'danger')
            except Exception as e:
                flash(f'Failed to change password: {str(e)}', 'danger')
            finally:
                con.close()
            return redirect(url_for('employee_profile', tab='security'))
            
        elif action == 'toggle_2fa':
            enabled = request.form.get('two_factor_enabled') == '1'
            toggle_user_2fa(user_id, enabled)
            log_activity(user_id, '2FA Toggle', f'Toggled two-factor authentication to {"Enabled" if enabled else "Disabled"}')
            flash(f'Two-factor authentication {"enabled" if enabled else "disabled"} successfully.', 'success')
            return redirect(url_for('employee_profile', tab='security'))
            
        elif action == 'upload_avatar':
            file = request.files.get('photo')
            if file and file.filename:
                filename = f"avatar_{user_id}_{secure_filename(file.filename)}"
                upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'avatars')
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, filename))
                avatar_url = f"/static/uploads/avatars/{filename}"
                update_employee_avatar(user_id, avatar_url)
                log_activity(user_id, 'Profile Update', 'Uploaded new avatar photo')
                flash('Profile photo updated successfully.', 'success')
            else:
                flash('No file selected.', 'danger')
            return redirect(url_for('employee_profile'))
            
        elif action == 'upload_document':
            file = request.files.get('document')
            doc_type = request.form.get('document_type')
            if file and file.filename and doc_type:
                filename = f"doc_{employee['id']}_{secure_filename(file.filename)}"
                upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'documents')
                os.makedirs(upload_dir, exist_ok=True)
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                
                size_bytes = os.path.getsize(filepath)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024*1024):.1f} MB"
                    
                replace_employee_document(employee['id'], doc_type, file.filename, size_str)
                log_activity(user_id, 'Document Upload', f'Uploaded document: {doc_type}')
                flash(f'Document {doc_type} uploaded successfully.', 'success')
            else:
                flash('Document file and type are required.', 'danger')
            return redirect(url_for('employee_profile', tab='documents'))
            
        elif action == 'create_inquiry':
            subject = request.form.get('subject')
            message = request.form.get('message')
            if subject and message:
                submit_inquiry(user_id, subject, message)
                log_activity(user_id, 'Inquiry Submitted', f'Created inquiry: {subject}')
                flash('Inquiry submitted successfully to HR.', 'success')
            else:
                flash('Subject and message are required.', 'danger')
            return redirect(url_for('employee_profile', tab='inquiries'))

    # GET requests - Gather data
    attendance_history = get_attendance_history(user_id)
    leaves = get_employee_leaves(user_id)
    payslips = get_employee_payslips(user_id)
    employee_docs = get_employee_documents(employee['id'])
    inquiries = get_employee_inquiries(user_id)
    activities = get_user_audit_logs(user_id, limit=20)
    
    # Calculate Attendance Statistics
    present_days = sum(1 for a in attendance_history if a.get('status', '').lower() in ['present', 'wfh'])
    absent_days = sum(1 for a in attendance_history if a.get('status', '').lower() in ['absent'])
    leave_days = sum(1 for a in attendance_history if a.get('status', '').lower() in ['leave', 'half_day'])
    
    total_att_records = len(attendance_history)
    att_percent = 100.0
    if total_att_records > 0:
        att_percent = round((present_days / total_att_records) * 100.0, 1)
        
    overtime_hours = sum(a.get('overtime_hours', 0.0) or 0.0 for a in attendance_history)
    late_arrivals = 0
    for a in attendance_history:
        ci = a.get('check_in')
        if ci:
            try:
                parts = ci.split(':')
                if len(parts) == 2:
                    h, m = int(parts[0]), int(parts[1])
                    if h > 9 or (h == 9 and m > 15):
                        late_arrivals += 1
            except:
                pass

    # Leave balance and counts
    leave_balance = get_leave_balance(user_id) or {'annual': 15, 'sick': 10, 'casual': 10}
    pending_leaves = sum(1 for l in leaves if l.get('status', '').lower() == 'pending')
    approved_leaves = sum(1 for l in leaves if l.get('status', '').lower() == 'approved')

    # Latest payslip
    latest_payslip = payslips[0] if payslips else None
    
    # Profile Completion calculations
    personal_fields = [employee.get('name'), employee.get('gender'), employee.get('date_of_birth'), 
                       employee.get('marital_status'), employee.get('blood_group'), employee.get('nationality'),
                       employee.get('aadhaar_number'), employee.get('pan_number')]
    personal_pct = int(sum(1 for f in personal_fields if f) / len(personal_fields) * 100)
    
    contact_fields = [employee.get('personal_email'), employee.get('email'), employee.get('phone'),
                      employee.get('alternate_phone'), employee.get('address'), 
                      employee.get('emergency_contact_name'), employee.get('emergency_contact_phone')]
    contact_pct = int(sum(1 for f in contact_fields if f) / len(contact_fields) * 100)
    
    payroll_fields = [employee.get('bank_name'), employee.get('bank_account'), employee.get('ifsc_code'),
                      employee.get('uan_number'), employee.get('esi_number'), employee.get('pf_number')]
    payroll_pct = int(sum(1 for f in payroll_fields if f) / len(payroll_fields) * 100)
    
    # Document Completion (we expect Aadhaar, PAN, Resume, Offer Letter)
    uploaded_types = {d.get('document_type') for d in employee_docs}
    required_doc_types = ['Aadhaar Card', 'PAN Card', 'Resume', 'Offer Letter']
    doc_pct = int(sum(1 for t in required_doc_types if t in uploaded_types) / len(required_doc_types) * 100)
    
    overall_pct = int((personal_pct + contact_pct + payroll_pct + doc_pct) / 4)

    # User 2FA info
    con = _get_con()
    two_factor = 0
    try:
        cur = con.cursor()
        cur.execute("SELECT two_factor_enabled FROM users WHERE id = ?", (user_id,))
        urow = cur.fetchone()
        if urow:
            two_factor = urow['two_factor_enabled'] or 0
    except:
        pass
    finally:
        con.close()

    # Dynamic Notifications
    notifications = []
    if overall_pct < 85:
        notifications.append({
            'type': 'warning',
            'message': f'Profile is only {overall_pct}% complete. Please fill outstanding fields to complete registration.',
            'link': '#personal'
        })
    for doc_type in ['Aadhaar Card', 'PAN Card', 'Resume']:
        if doc_type not in uploaded_types:
            notifications.append({
                'type': 'danger',
                'message': f'Mandatory document "{doc_type}" is missing. Please upload it immediately.',
                'link': '#documents'
            })
    if latest_payslip:
        notifications.append({
            'type': 'info',
            'message': f'Your payslip for {get_month_name(latest_payslip["month"])} {latest_payslip["year"]} is generated.',
            'link': '#payroll'
        })
    if pending_leaves > 0:
        notifications.append({
            'type': 'info',
            'message': f'You have {pending_leaves} pending leave request(s) awaiting review.',
            'link': '#leaves'
        })
        
    # Mock some default activities if None
    if not activities:
        activities = [
            {'timestamp': str(datetime.datetime.now() - datetime.timedelta(hours=2))[:19], 'action': 'Login Success', 'details': 'Signed in from Chrome on Windows'},
            {'timestamp': str(datetime.datetime.now() - datetime.timedelta(days=1))[:19], 'action': 'Profile Update', 'details': 'Updated personal details'},
            {'timestamp': str(datetime.datetime.now() - datetime.timedelta(days=3))[:19], 'action': 'Payslip Download', 'details': 'Downloaded payslip for May 2026'}
        ]

    # Mask account number
    masked_account = ''
    raw_account = employee.get('bank_account') or ''
    if raw_account:
        if len(raw_account) > 4:
            masked_account = '*' * (len(raw_account) - 4) + raw_account[-4:]
        else:
            masked_account = raw_account

    return render_template(
        'employee/profile.html',
        employee=employee,
        attendance_history=attendance_history[:10],
        present_days=present_days,
        absent_days=absent_days,
        leave_days=leave_days,
        attendance_percentage=att_percent,
        overtime_hours=round(overtime_hours, 2),
        late_arrivals=late_arrivals,
        leaves=leaves[:10],
        leave_balance=leave_balance,
        pending_leaves=pending_leaves,
        approved_leaves=approved_leaves,
        payslips=payslips,
        latest_payslip=latest_payslip,
        employee_docs=employee_docs,
        inquiries=inquiries,
        activities=activities,
        personal_pct=personal_pct,
        contact_pct=contact_pct,
        payroll_pct=payroll_pct,
        doc_pct=doc_pct,
        overall_pct=overall_pct,
        two_factor_enabled=two_factor,
        notifications=notifications,
        masked_account=masked_account
    )

@app.route('/employee/profile/pdf')
@employee_required
def employee_profile_pdf():
    user_id = session.get('user_id')
    employee = get_employee_by_user_id(user_id)
    if not employee:
        flash('Employee profile not found.', 'danger')
        return redirect(url_for('employee_dashboard'))
        
    payslips = get_employee_payslips(user_id)
    latest_payslip = payslips[0] if payslips else None
    
    # Mask account number
    masked_account = ''
    raw_account = employee.get('bank_account') or ''
    if raw_account:
        if len(raw_account) > 4:
            masked_account = '*' * (len(raw_account) - 4) + raw_account[-4:]
        else:
            masked_account = raw_account
            
    return render_template(
        'employee/profile_pdf.html',
        employee=employee,
        latest_payslip=latest_payslip,
        masked_account=masked_account
    )


@app.route('/employee/attendance', methods=['GET', 'POST'])
@employee_required
def employee_attendance():
    user_id = session.get('user_id')
    
    form = AttendanceForm()
    if form.validate_on_submit():
        # Check if attendance already marked for today
        if check_attendance_today(user_id):
            flash('Attendance already marked for today', 'warning')
        else:
            mark_attendance(user_id, form.status.data, form.note.data)
            flash('Attendance marked successfully', 'success')
        return redirect(url_for('employee_attendance'))
    
    # Get attendance history
    attendance_history = get_attendance_history(user_id)
    
    # Check if attendance already marked for today
    attendance_marked_today = check_attendance_today(user_id)
    
    # Get attendance percentage
    attendance_percentage = calculate_attendance_percentage(user_id)
    
    return render_template('employee/attendance.html', 
                          form=form, 
                          attendance_history=attendance_history,
                          attendance_marked_today=attendance_marked_today,
                          attendance_percentage=attendance_percentage)

@app.route('/employee/apply-leave', methods=['GET', 'POST'])
@employee_required
def apply_leave():
    user_id = session.get('user_id')
    
    form = LeaveApplicationForm()
    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
        leave_type = form.leave_type.data
        reason = form.reason.data
        
        if start_date > end_date:
            flash('End date must be after start date', 'danger')
        elif start_date < datetime.datetime.now().date():
            flash('Start date cannot be in the past', 'danger')
        else:
            try:
                apply_for_leave(user_id, start_date, end_date, leave_type, reason)
                flash('Leave application submitted successfully', 'success')
                return redirect(url_for('my_leaves'))
            except Exception as e:
                flash(f'Error submitting leave request: {str(e)}', 'danger')
                app.logger.error(f"Leave request error: {str(e)}")
    
    return render_template('employee/apply_leave.html', form=form)

@app.route('/employee/leaves')
@employee_required
def my_leaves():
    user_id = session.get('user_id')
    leave_requests = get_employee_leaves(user_id)
    leave_balance = get_leave_balance(user_id)
    
    return render_template('employee/leaves.html', leave_requests=leave_requests, leave_balance=leave_balance)

@app.route('/employee/payroll')
@employee_required
def payroll_history():
    user_id = session.get('user_id')
    payslips = get_employee_payslips(user_id)
    
    return render_template('employee/payroll.html', payslips=payslips)

@app.route('/employee/inquiry', methods=['GET', 'POST'])
@employee_required
def employee_inquiry():
    user_id = session.get('user_id')
    
    form = InquiryForm()
    if form.validate_on_submit():
        subject = form.subject.data
        message = form.message.data
        
        try:
            submit_inquiry(user_id, subject, message)
            flash('Inquiry submitted successfully', 'success')
            return redirect(url_for('employee_inquiry'))
        except Exception as e:
            flash(f'Error submitting inquiry: {str(e)}', 'danger')
            app.logger.error(f"Inquiry submission error: {str(e)}")
        
        submit_inquiry(user_id, subject, message)
        flash('Inquiry submitted successfully', 'success')
        return redirect(url_for('employee_inquiry'))
    
    # Get previous inquiries
    inquiries = get_employee_inquiries(user_id)
    
    return render_template('employee/inquiry.html', form=form, inquiries=inquiries)

# HR routes
@app.route('/hr/dashboard')
@hr_required
def hr_dashboard():
    # Get dashboard stats
    total_employees = get_total_employees()
    pending_leaves = get_total_pending_leaves()
    monthly_payroll = get_monthly_payroll_amount()
    recent_activities = get_recent_activities()
    
    return render_template('hr/dashboard.html',
                          total_employees=total_employees,
                          pending_leaves=pending_leaves,
                          monthly_payroll=monthly_payroll,
                          recent_activities=recent_activities,
                          get_filtered_inquiries=get_filtered_inquiries)

@app.route('/hr/employees', methods=['GET', 'POST'])
@hr_required
def employee_management():
    form = AddEmployeeForm()
    
    if request.method == 'POST':
        # Retrieve all input values
        name = request.form.get('name')
        personal_email = request.form.get('personal_email')
        corporate_email = request.form.get('corporate_email')
        gender = request.form.get('gender', 'Male')
        date_of_birth = request.form.get('date_of_birth')
        phone = request.form.get('phone')
        
        department = request.form.get('department')
        designation = request.form.get('designation')
        branch = request.form.get('branch', 'Main Headquarters')
        reporting_manager = request.form.get('reporting_manager', 'Admin User')
        employee_type = request.form.get('employee_type', 'Full-Time')
        date_joined = request.form.get('date_joined')
        probation_status = request.form.get('probation_status', 'Probation')
        
        salary = request.form.get('salary', '3000.00')
        bank_account = request.form.get('bank_account')
        ifsc_code = request.form.get('ifsc_code')
        pan_number = request.form.get('pan_number')
        aadhaar_number = request.form.get('aadhaar_number')
        uan_number = request.form.get('uan_number')
        esi_number = request.form.get('esi_number')
        
        # Uniqueness checks
        con = _get_con()
        try:
            cur = con.cursor()
            cur.execute("SELECT id FROM users WHERE email = ?", (corporate_email,))
            if cur.fetchone():
                flash(f'Error: Corporate email {corporate_email} is already registered.', 'danger')
                return redirect(url_for('employee_management'))
        finally:
            con.close()
            
        # Generate Employee Code & Username
        employee_code = generate_next_employee_code()
        username = generate_username_from_name(name)
        temp_password = "Emp@123"
        password_hash = generate_password_hash(temp_password)
        
        # Create User
        con = _get_con()
        try:
            cur = con.cursor()
            now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert user with force_password_change = 1
            cur.execute(
                """
                INSERT INTO users (name, email, password, role, created_at, force_password_change)
                VALUES (?, ?, ?, 'employee', ?, 1)
                """,
                (name, corporate_email, password_hash, now_str)
            )
            user_id = cur.lastrowid
            
            # Insert employee
            cur.execute(
                """
                INSERT INTO employees (
                    user_id, department, designation, address, phone, emergency_contact,
                    date_of_birth, date_joined, basic_salary, status, uan_number, esi_number,
                    pan_number, aadhaar_number, state, pf_status, esi_status, pt_status,
                    gender, marital_status, blood_group, nationality, alternate_phone,
                    employee_code, branch, reporting_manager, employee_type, probation_status,
                    salary_structure, bank_account, ifsc_code, pf_number, tax_info
                ) VALUES (
                    ?, ?, ?, '', ?, '',
                    ?, ?, ?, 'active', ?, ?,
                    ?, ?, 'Maharashtra', 'Active', 'Active', 'Active',
                    ?, 'Single', 'O+', 'Indian', '',
                    ?, ?, ?, ?, ?,
                    'Standard Class', ?, ?, '', 'Single Filer'
                )
                """,
                (user_id, department, designation, phone,
                 date_of_birth, date_joined, float(salary), uan_number, esi_number,
                 pan_number, aadhaar_number, gender,
                 employee_code, branch, reporting_manager, employee_type, probation_status,
                 bank_account, ifsc_code)
            )
            employee_id = cur.lastrowid
            
            # Insert Payroll Profile
            cur.execute(
                """
                INSERT INTO payroll_profiles (
                    employee_id, salary_structure, basic_salary, bank_account, ifsc_code,
                    uan_number, esi_number, pf_number, pan_number, aadhaar_number
                ) VALUES (?, 'Standard Class', ?, ?, ?, ?, ?, '', ?, ?)
                """,
                (employee_id, float(salary), bank_account, ifsc_code, uan_number, esi_number, pan_number, aadhaar_number)
            )
            
            # Insert Attendance Profile
            cur.execute(
                """
                INSERT INTO attendance_profiles (employee_id, shift, location, working_hours_per_day)
                VALUES (?, 'General', 'Office', 8.0)
                """,
                (employee_id,)
            )
            
            # Log lifecycle onboarding event
            cur.execute(
                """
                INSERT INTO employee_lifecycle (employee_id, event_type, event_date, description, performed_by)
                VALUES (?, 'Onboarding', ?, 'Employee profile created and corporate systems initialized.', 'Admin User')
                """,
                (employee_id, date_joined)
            )
            
            con.commit()
            
            # Store details in session to render the success modal popup on redirect
            session['new_emp_created'] = {
                'code': employee_code,
                'username': username,
                'password': temp_password,
                'name': name
            }
            
            flash('Employee profile and system accounts successfully generated!', 'success')
        except Exception as e:
            con.rollback()
            flash(f'Database registration failed: {str(e)}', 'danger')
        finally:
            con.close()
            
        return redirect(url_for('employee_management'))
    
    employees = get_all_employees()
    stats = get_employee_dashboard_stats()
    new_emp = session.pop('new_emp_created', None)
    
    return render_template('hr/employee_management.html', form=form, employees=employees, stats=stats, new_emp=new_emp)

@app.route('/hr/employees/<int:employee_id>', methods=['GET', 'POST'])
@hr_required
def edit_employee(employee_id):
    employee = get_employee_by_id(employee_id)
    if not employee:
        flash('Employee not found', 'danger')
        return redirect(url_for('employee_management'))
    
    form = EditEmployeeForm()
    
    if request.method == 'POST':
        action = request.form.get('action_type')
        
        # 1. Update Profile Action
        if action == 'update_profile':
            update_employee_profile_hr(
                employee_id=employee_id,
                name=request.form.get('name'),
                gender=request.form.get('gender', 'Male'),
                marital_status=request.form.get('marital_status', 'Single'),
                blood_group=request.form.get('blood_group', 'O+'),
                nationality=request.form.get('nationality', 'Indian'),
                phone=request.form.get('phone', ''),
                alternate_phone=request.form.get('alternate_phone', ''),
                address=request.form.get('address', ''),
                emergency_contact=request.form.get('emergency_contact', ''),
                employee_code=request.form.get('employee_code', ''),
                department=request.form.get('department'),
                designation=request.form.get('designation'),
                branch=request.form.get('branch', 'Main Headquarters'),
                reporting_manager=request.form.get('reporting_manager', 'Admin User'),
                employee_type=request.form.get('employee_type', 'Full-Time'),
                probation_status=request.form.get('probation_status', 'Confirmed'),
                salary=request.form.get('salary', employee.get('basic_salary')),
                salary_structure=request.form.get('salary_structure', 'Standard Class'),
                bank_account=request.form.get('bank_account', ''),
                ifsc_code=request.form.get('ifsc_code', ''),
                pf_number=request.form.get('pf_number', ''),
                uan_number=request.form.get('uan_number', ''),
                esi_number=request.form.get('esi_number', ''),
                tax_info=request.form.get('tax_info', 'Single Filer'),
                status=request.form.get('status', employee.get('status'))
            )
            flash('Employee profile updated successfully', 'success')
            return redirect(url_for('edit_employee', employee_id=employee_id))
            
        # 2. Reset Password Action
        elif action == 'reset_password':
            con = _get_con()
            try:
                cur = con.cursor()
                pwd = generate_password_hash("password123")
                cur.execute("UPDATE users SET password = ? WHERE id = ?", (pwd, employee['user_id']))
                con.commit()
                flash('Password reset to default (password123) successfully.', 'success')
            finally:
                con.close()
            return redirect(url_for('edit_employee', employee_id=employee_id))
            
        # 3. Lifecycle events
        elif action in ['promote', 'transfer', 'terminate', 'deactivate']:
            desc = ""
            perf_by = session.get('user_name', 'HR Admin') or 'HR Admin'
            
            if action == 'promote':
                new_designation = request.form.get('new_designation')
                new_salary = request.form.get('new_salary')
                desc = f"Promoted to {new_designation} with salary ${new_salary}."
                con = _get_con()
                try:
                    cur = con.cursor()
                    cur.execute("UPDATE employees SET designation = ?, basic_salary = ? WHERE id = ?", (new_designation, float(new_salary), employee_id))
                    con.commit()
                finally:
                    con.close()
                add_lifecycle_event(employee_id, 'Promotion', desc, perf_by)
                flash('Employee promoted successfully.', 'success')
                
            elif action == 'transfer':
                new_dept = request.form.get('new_department')
                new_branch = request.form.get('new_branch')
                new_manager = request.form.get('new_manager')
                desc = f"Transferred to {new_dept} department at {new_branch} under {new_manager}."
                con = _get_con()
                try:
                    cur = con.cursor()
                    cur.execute("UPDATE employees SET department = ?, branch = ?, reporting_manager = ? WHERE id = ?", (new_dept, new_branch, new_manager, employee_id))
                    con.commit()
                finally:
                    con.close()
                add_lifecycle_event(employee_id, 'Transfer', desc, perf_by)
                flash('Employee transferred successfully.', 'success')
                
            elif action == 'terminate':
                reason = request.form.get('exit_reason')
                desc = f"Terminated/Exited. Reason: {reason}."
                con = _get_con()
                try:
                    cur = con.cursor()
                    cur.execute("UPDATE employees SET status = 'resigned' WHERE id = ?", (employee_id,))
                    con.commit()
                finally:
                    con.close()
                add_lifecycle_event(employee_id, 'Termination', desc, perf_by)
                flash('Employee status updated to exited/resigned.', 'success')
                
            elif action == 'deactivate':
                desc = "Account deactivated."
                con = _get_con()
                try:
                    cur = con.cursor()
                    cur.execute("UPDATE employees SET status = 'inactive' WHERE id = ?", (employee_id,))
                    con.commit()
                finally:
                    con.close()
                add_lifecycle_event(employee_id, 'Deactivation', desc, perf_by)
                flash('Employee account deactivated.', 'success')
                
            return redirect(url_for('edit_employee', employee_id=employee_id))
            
        # 4. Upload Document
        elif action == 'upload_doc':
            doc_type = request.form.get('doc_type')
            file_name = request.form.get('file_name')
            if not file_name:
                file_name = f'{doc_type.lower().replace(" ", "_")}.pdf'
            file_size = "1.5 MB"
            add_employee_document(employee_id, doc_type, file_name, file_size)
            flash(f'Document {doc_type} uploaded successfully (simulated).', 'success')
            return redirect(url_for('edit_employee', employee_id=employee_id))

        # 5. Delete Document
        elif action == 'delete_doc':
            doc_id = int(request.form.get('doc_id'))
            delete_employee_document(doc_id)
            flash('Document deleted successfully.', 'success')
            return redirect(url_for('edit_employee', employee_id=employee_id))
            
    # Load history data
    attendance_history = get_attendance_history(employee['user_id'])
    leave_history = get_employee_leaves(employee['user_id'])
    payslip_history = get_employee_payslips(employee['user_id'])
    
    # Load document and lifecycle logs
    documents = get_employee_documents(employee_id)
    lifecycle_history = get_employee_lifecycle(employee_id)
    
    # Calculate attendance stats
    total_present = sum(1 for a in attendance_history if a['status'] in ['present', 'wfh'])
    total_absent = sum(1 for a in attendance_history if a['status'] == 'absent')
    total_half_day = sum(1 for a in attendance_history if a['status'] == 'half_day')
    
    total_records = len(attendance_history)
    attendance_pct = round((total_present + total_half_day * 0.5) / total_records * 100, 2) if total_records > 0 else 100.00
    
    form.name.data = employee.get('name')
    form.status.data = employee.get('status')
    form.department.data = employee.get('department')
    form.designation.data = employee.get('designation')
    form.salary.data = employee.get('basic_salary')
    
    return render_template(
        'hr/edit_employee.html', 
        form=form, 
        employee=employee,
        attendance_history=attendance_history,
        leave_history=leave_history,
        payslip_history=payslip_history,
        documents=documents,
        lifecycle_history=lifecycle_history,
        total_present=total_present,
        total_absent=total_absent,
        total_half_day=total_half_day,
        attendance_pct=attendance_pct
    )

@app.route('/api/download/employees/csv')
@hr_required
def download_employees_csv():
    import csv
    from io import StringIO
    from flask import make_response
    
    employees = get_all_employees()
    
    try:
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Employee ID', 'Employee Code', 'Full Name', 'Email', 'Gender', 'Date of Birth',
            'Department', 'Designation', 'Branch', 'Reporting Manager', 'Joining Date',
            'Employment Type', 'Probation Status', 'Basic Salary', 'Bank Account', 'IFSC Code',
            'UAN Number', 'ESI Number', 'PF Number', 'Status'
        ])
        
        for emp in employees:
            writer.writerow([
                emp.get('id'),
                emp.get('employee_code', ''),
                emp.get('name'),
                emp.get('email'),
                emp.get('gender', 'Male'),
                emp.get('date_of_birth', ''),
                emp.get('department'),
                emp.get('designation'),
                emp.get('branch', 'Main Headquarters'),
                emp.get('reporting_manager', 'Admin User'),
                emp.get('date_joined'),
                emp.get('employee_type', 'Full-Time'),
                emp.get('probation_status', 'Confirmed'),
                f"${emp.get('basic_salary'):.2f}",
                emp.get('bank_account', ''),
                emp.get('ifsc_code', ''),
                emp.get('uan_number', ''),
                emp.get('esi_number', ''),
                emp.get('pf_number', ''),
                emp.get('status')
            ])
            
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=employee_directory.csv'
        return response
    except Exception as e:
        app.logger.error(f"Failed to export employees CSV: {str(e)}")
        return jsonify({'error': 'CSV export failed'}), 500

@app.route('/api/download/employee/pdf/<int:employee_id>')
@hr_required
def download_employee_profile_pdf(employee_id):
    employee = get_employee_by_id(employee_id)
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
        
    try:
        now = datetime.datetime.now()
        return render_template(
            'hr/employee_profile_pdf.html',
            employee=employee,
            now=now
        )
    except Exception as e:
        return str(e), 500

@app.route('/hr/employees/delete/<int:employee_id>', methods=['POST'])
@hr_required
def delete_employee(employee_id):
    delete_employee_by_id(employee_id)
    flash('Employee deleted successfully', 'success')
    return redirect(url_for('employee_management'))

@app.route('/hr/attendance')
@hr_required
def attendance_monitoring():
    employees = get_all_employees()
    
    # Get filters
    date_filter = request.args.get('date', datetime.datetime.now().strftime('%Y-%m-%d'))
    employee_filter = request.args.get('employee', '')
    department_filter = request.args.get('department', '')
    status_filter = request.args.get('status', '')
    shift_filter = request.args.get('shift', '')
    
    # Fetch filtered attendance
    attendance_records = get_filtered_attendance(
        date_filter, employee_filter, department_filter, status_filter, shift_filter
    )
    
    # Total active employees count
    total_employees = len(get_all_active_employees())
    if total_employees == 0:
        total_employees = len(employees)
        
    present_today = len([r for r in attendance_records if r['status'] in ['present', 'wfh']])
    absent_today = len([r for r in attendance_records if r['status'] == 'absent'])
    half_day_today = len([r for r in attendance_records if r['status'] == 'half_day'])
    wfh_today = len([r for r in attendance_records if r['status'] == 'wfh'])
    
    # Calculate late arrivals
    late_today = len([r for r in attendance_records if (r['note'] and 'late' in r['note'].lower())])
    
    # Calculate overtime
    overtime_today = len([r for r in attendance_records if (r['overtime_hours'] or 0) > 0])
    
    # On leave today
    on_leave_today = len([r for r in attendance_records if r['status'] == 'leave'])
    
    # Calculate early departures (checked out before 5:00 PM / 17:00)
    early_today = len([r for r in attendance_records if r['check_out'] and r['check_out'] < '17:00' and r['status'] in ['present', 'half_day']])
    
    # Attendance percentage
    attendance_percentage = round(((present_today + half_day_today + wfh_today) / total_employees * 100), 1) if total_employees > 0 else 0.0
    
    # Query last 7 days trend
    con = _get_con()
    trend_labels = []
    trend_present = []
    trend_absent = []
    try:
        cur = con.cursor()
        for i in range(6, -1, -1):
            d = (datetime.datetime.now() - datetime.timedelta(days=i)).date()
            cur.execute("SELECT COUNT(*) AS c FROM attendance WHERE date = ? AND status IN ('present', 'wfh')", (str(d),))
            p_count = cur.fetchone()['c']
            cur.execute("SELECT COUNT(*) AS c FROM attendance WHERE date = ? AND status = 'absent'", (str(d),))
            a_count = cur.fetchone()['c']
            trend_labels.append(d.strftime('%b %d'))
            trend_present.append(p_count)
            trend_absent.append(a_count)
    finally:
        con.close()
        
    # Department stats
    dept_labels = ['HR', 'IT', 'Finance', 'Marketing', 'Operations', 'Sales']
    dept_values = []
    con = _get_con()
    try:
        cur = con.cursor()
        for d in dept_labels:
            cur.execute(
                """
                SELECT COUNT(*) AS c 
                FROM attendance a
                JOIN employees e ON a.employee_id = e.id
                WHERE a.date = ? AND e.department = ? AND a.status IN ('present', 'wfh')
                """,
                (date_filter, d)
            )
            dept_values.append(cur.fetchone()['c'])
    finally:
        con.close()
        
    return render_template('hr/attendance_monitor.html',
                          employees=employees,
                          attendance_records=attendance_records,
                          date_filter=date_filter,
                          employee_filter=employee_filter,
                          department_filter=department_filter,
                          status_filter=status_filter,
                          shift_filter=shift_filter,
                          total_employees=total_employees,
                          present_today=present_today,
                          absent_today=absent_today,
                          half_day_today=half_day_today,
                          wfh_today=wfh_today,
                          late_today=late_today,
                          overtime_today=overtime_today,
                          on_leave_today=on_leave_today,
                          early_today=early_today,
                          attendance_percentage=attendance_percentage,
                          trend_labels=trend_labels,
                          trend_present=trend_present,
                          trend_absent=trend_absent,
                          dept_labels=dept_labels,
                          dept_values=dept_values)

@app.route('/hr/attendance/update', methods=['POST'])
@hr_required
def update_attendance():
    attendance_id = request.form.get('attendance_id')
    status = request.form.get('status')
    
    update_attendance_status(attendance_id, status)
    flash('Attendance updated successfully', 'success')
    return redirect(url_for('attendance_monitoring'))

@app.route('/hr/leaves')
@hr_required
def leave_management():
    # Get filter options
    status_filter = request.args.get('status', 'pending')
    department_filter = request.args.get('department', '')
    
    logging.info(f"Admin query: Fetching leaves with status='{status_filter}', department='{department_filter}'")
    
    # Fetch filtered requests
    all_filtered_requests = get_filtered_leave_requests(status_filter, department_filter)
    
    logging.info(f"Admin query results: Found {len(all_filtered_requests)} filtered leave requests")
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 10
    total_records = len(all_filtered_requests)
    total_pages = (total_records + per_page - 1) // per_page
    leave_requests = all_filtered_requests[(page - 1) * per_page : page * per_page]
    
    # Compute dashboard metrics
    leave_stats = get_leave_stats()
    leave_type_counts = get_leave_type_distribution()
    dept_leave_counts = get_department_leave_analysis()
    
    # Retrieve all employees to populate full list of departments in the filter
    employees = get_all_employees()
    audit_logs = get_audit_logs(limit=10)
    
    return render_template('hr/leave_approvals.html',
                          leave_requests=leave_requests,
                          status_filter=status_filter,
                          department_filter=department_filter,
                          leave_stats=leave_stats,
                          leave_type_counts=leave_type_counts,
                          dept_leave_counts=dept_leave_counts,
                          employees=employees,
                          audit_logs=audit_logs,
                          page=page,
                          total_pages=total_pages,
                          total_records=total_records)

@app.route('/hr/leaves/update', methods=['POST'])
@hr_required
def update_leave_status():
    leave_id = request.form.get('leave_id')
    status = request.form.get('status')
    comment = request.form.get('comment', '')
    admin_user_id = session.get('user_id')
    
    logging.info(f"Admin approval action: admin_user_id={admin_user_id} updating leave_id={leave_id} to status={status}")
    
    update_leave_request_status(leave_id, status, comment, admin_user_id=admin_user_id)
    flash(f'Leave request has been {status} successfully', 'success')
    return redirect(url_for('leave_management'))

@app.route('/hr/payroll')
@hr_required
def payroll_processing():
    # Get current month/year for processing
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    
    month = int(request.args.get('month', current_month))
    year = int(request.args.get('year', current_year))
    
    # Get employees for payroll processing
    employees = get_all_active_employees()
    
    # Check if payroll has been processed for the month
    is_processed = check_payroll_processed(month, year)
    
    # Import get_month_name from utils
    from utils import get_month_name
    
    return render_template('hr/payroll_processing.html',
                          employees=employees,
                          month=month,
                          year=year,
                          is_processed=is_processed,
                          get_month_name=get_month_name)

@app.route('/hr/payroll/process', methods=['POST'])
@hr_required
def process_payroll():
    month = int(request.form.get('month'))
    year = int(request.form.get('year'))
    
    # Process payroll for all employees
    process_monthly_payroll(month, year)
    
    flash('Payroll processed successfully for {}/{}'.format(month, year), 'success')
    return redirect(url_for('payroll_processing'))

@app.route('/hr/payslips')
@hr_required
def payslip_management():
    # Get filter options
    month = int(request.args.get('month', datetime.datetime.now().month))
    year = int(request.args.get('year', datetime.datetime.now().year))
    employee_id = request.args.get('employee', '')
    
    # Get all employees for filter dropdown
    employees = get_all_employees()
    
    # Fix: lookup employee profile id or pass user_id appropriately
    # The dropdown uses employee.id (profile ID), let's ensure it maps correctly
    
    # Get payslips based on filters
    all_filtered_payslips = get_filtered_payslips(month, year, employee_id)
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 10
    total_records = len(all_filtered_payslips)
    total_pages = (total_records + per_page - 1) // per_page
    payslips = all_filtered_payslips[(page - 1) * per_page : page * per_page]
    
    # Aggregate Metrics & Analytics Charts data
    payslip_stats = get_payslip_stats(month, year)
    dept_salary_distribution = get_department_salary_distribution(month, year)
    payroll_monthly_trend = get_payroll_monthly_trend()
    
    # Import get_month_name from utils
    from utils import get_month_name
    
    return render_template('hr/payslip_generator.html',
                          payslips=payslips,
                          employees=employees,
                          month=month,
                          year=year,
                          employee_id=employee_id,
                          payslip_stats=payslip_stats,
                          dept_salary_distribution=dept_salary_distribution,
                          payroll_monthly_trend=payroll_monthly_trend,
                          page=page,
                          total_pages=total_pages,
                          total_records=total_records,
                          get_month_name=get_month_name)

@app.route('/hr/payslips/status/<int:payslip_id>', methods=['POST'])
@hr_required
def update_payslip_approval(payslip_id):
    status = request.form.get('status')
    update_payslip_status(payslip_id, status)
    flash(f'Payslip status updated to {status}', 'success')
    return redirect(url_for('payslip_management'))

@app.route('/hr/payslips/regenerate/<int:payslip_id>', methods=['POST'])
@hr_required
def regenerate_payslip(payslip_id):
    # Fetch details first
    payslip = get_payslip_by_id(payslip_id)
    if not payslip:
        flash('Payslip not found', 'danger')
        return redirect(url_for('payslip_management'))
        
    process_monthly_payroll(payslip['month'], payslip['year'], target_employee_id=payslip['employee_id'])
    flash('Payslip regenerated successfully', 'success')
    return redirect(url_for('payslip_management'))

@app.route('/hr/compliance-reports')
@hr_required
def compliance_reports():
    # Get filter options
    month = int(request.args.get('month', datetime.datetime.now().month))
    year = int(request.args.get('year', datetime.datetime.now().year))
    report_type = request.args.get('type', 'pf')
    
    # Generate report data
    report_data = generate_compliance_report(month, year, report_type)
    
    # Get additional compliance datasets
    compliance_stats = get_compliance_dashboard_stats(month, year)
    compliance_alerts = get_compliance_alerts()
    compliance_filings = get_compliance_filings()
    
    # Import get_month_name from utils
    from utils import get_month_name
    
    return render_template('hr/compliance_reports.html',
                          report_data=report_data,
                          month=month,
                          year=year,
                          report_type=report_type,
                          get_month_name=get_month_name,
                          compliance_stats=compliance_stats,
                          compliance_alerts=compliance_alerts,
                          compliance_filings=compliance_filings)

@app.route('/hr/compliance-reports/action', methods=['POST'])
@hr_required
def compliance_action():
    action = request.form.get('action')
    report_type = request.form.get('type')
    month = int(request.form.get('month', datetime.datetime.now().month))
    year = int(request.form.get('year', datetime.datetime.now().year))
    
    user_name = session.get('user_name', 'HR Admin') or 'HR Admin'
            
    if action == 'file':
        mark_compliance_filed(report_type, month, year, user_name)
        flash(f'Compliance report for {report_type.upper()} ({get_month_name(month)} {year}) successfully marked as Filed.', 'success')
        
    return redirect(url_for('compliance_reports', month=month, year=year, type=report_type))

@app.route('/hr/inquiries')
@hr_required
def inquiry_management():
    # Get filter options
    status_filter = request.args.get('status', 'pending')
    
    # Get inquiries based on filter
    all_filtered_inquiries = get_filtered_inquiries(status_filter)
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 10
    total_records = len(all_filtered_inquiries)
    total_pages = (total_records + per_page - 1) // per_page
    inquiries = all_filtered_inquiries[(page - 1) * per_page : page * per_page]
    
    # Aggregate stats and chart distribution
    inquiry_stats = get_inquiry_stats()
    inquiry_category_distribution = get_inquiry_category_distribution()
    
    # Fetch HR staff users to assign to (mock list of names)
    hr_staff = ['Admin User', 'Jane Smith (HR Lead)', 'Robert Martin (HR Recruiter)', 'Alice Johnson (HR Coordinator)']
    
    return render_template('hr/inquiry_management.html',
                          inquiries=inquiries,
                          status_filter=status_filter,
                          inquiry_stats=inquiry_stats,
                          inquiry_category_distribution=inquiry_category_distribution,
                          hr_staff=hr_staff,
                          page=page,
                          total_pages=total_pages,
                          total_records=total_records)

@app.route('/hr/inquiries/action', methods=['POST'])
@hr_required
def respond_to_inquiry():
    inquiry_id = int(request.form.get('inquiry_id'))
    action = request.form.get('action')
    
    con = _get_con()
    try:
        cur = con.cursor()
        now_str = str(datetime.datetime.now())
        if action == 'reply':
            response = request.form.get('response')
            cur.execute(
                "UPDATE inquiries SET response = ?, response_date = ?, status = 'resolved', last_updated = ? WHERE id = ?",
                (response, now_str, now_str, inquiry_id)
            )
            flash('Response sent successfully and inquiry marked as Resolved', 'success')
        elif action == 'status':
            status = request.form.get('status')
            cur.execute(
                "UPDATE inquiries SET status = ?, last_updated = ? WHERE id = ?",
                (status, now_str, inquiry_id)
            )
            flash(f'Inquiry status updated to {status.replace("_", " ").title()}', 'success')
        elif action == 'assign':
            assigned_to = request.form.get('assigned_to')
            cur.execute(
                "UPDATE inquiries SET assigned_to = ?, last_updated = ? WHERE id = ?",
                (assigned_to, now_str, inquiry_id)
            )
            flash(f'Inquiry assigned to {assigned_to}', 'success')
        elif action == 'escalate':
            cur.execute(
                "UPDATE inquiries SET priority = 'High', last_updated = ? WHERE id = ?",
                (now_str, inquiry_id)
            )
            flash('Inquiry escalated to High Priority', 'warning')
        con.commit()
    finally:
        con.close()
        
    return redirect(url_for('inquiry_management'))

# API routes for downloading
@app.route('/api/download/payslip/<int:payslip_id>')
def download_payslip(payslip_id):
    user_id = session.get('user_id')
    role = session.get('role')
    
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    payslip = get_payslip_by_id(payslip_id)
    if not payslip:
        return jsonify({'error': 'Payslip not found'}), 404
        
    # Secure check: resolve employee_id from user_id
    employee = get_employee_by_user_id(user_id)
    if role != 'hr' and (not employee or payslip['employee_id'] != employee['id']):
        return jsonify({'error': 'Access denied'}), 403
        
    # Generate HTML content from template
    html_content = render_template('payslip_pdf.html', payslip=payslip)
    
    # Attempt to convert HTML to PDF using pdfkit
    try:
        import pdfkit
        pdf = pdfkit.from_string(html_content, False)
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=Payslip-{payslip["month"]}-{payslip["year"]}.pdf'
        return response
    except Exception as e:
        app.logger.warning(f"PDF generation failed, falling back to HTML view: {str(e)}")
        # Fallback: Render the HTML template directly in the browser
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        return response

# API routes for compliance reports download
@app.route('/api/download/compliance/pdf')
@hr_required
def download_compliance_pdf():
    import pdfkit
    from flask import make_response
    
    month = request.args.get('month', default=datetime.datetime.now().month, type=int)
    year = request.args.get('year', default=datetime.datetime.now().year, type=int)
    report_type = request.args.get('type', default='pf')
    
    # Generate the report data
    report_data = generate_compliance_report(month, year, report_type)
    
    if not report_data or not report_data.get('employees'):
        return jsonify({'error': 'No report data available'}), 404
    
    try:
        # Prepare data for the template
        now = datetime.datetime.now()
        
        # Render the HTML template for PDF
        html = render_template('hr/compliance_pdf.html', 
                             report_data=report_data,
                             month=month,
                             year=year,
                             report_type=report_type,
                             get_month_name=get_month_name,
                             now=now)
        
        # Configuration for wkhtmltopdf
        options = {
            'page-size': 'Letter',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
        }
        
        # Generate PDF from HTML
        pdf = pdfkit.from_string(html, False, options=options)
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report_{month}_{year}.pdf'
        
        return response
    except Exception as e:
        app.logger.warning(f"PDF generation failed, falling back to HTML view: {str(e)}")
        response = make_response(html)
        response.headers['Content-Type'] = 'text/html'
        return response

@app.route('/api/download/compliance/csv')
@hr_required
def download_compliance_csv():
    import csv
    from io import StringIO
    from flask import make_response
    
    month = request.args.get('month', default=datetime.datetime.now().month, type=int)
    year = request.args.get('year', default=datetime.datetime.now().year, type=int)
    report_type = request.args.get('type', default='pf')
    
    # Generate the report data
    report_data = generate_compliance_report(month, year, report_type)
    
    if not report_data or not report_data.get('employees'):
        return jsonify({'error': 'No report data available'}), 404
    
    try:
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header and data rows based on report_type
        if report_type == 'pf':
            writer.writerow(['Employee ID', 'Name', 'UAN Number', 'PF Wages', 'Employee Contribution', 'Employer Contribution', 'Total PF Amount', 'Filing Status'])
            for employee in report_data['employees']:
                writer.writerow([
                    employee['id'],
                    employee['name'],
                    employee['uan_number'],
                    f"${employee['pf_wages']:.2f}",
                    f"${employee['employee_contribution']:.2f}",
                    f"${employee['employer_contribution']:.2f}",
                    f"${employee['total_pf']:.2f}",
                    employee['filing_status']
                ])
            writer.writerow(['', '', 'Total', f"${report_data['total_pf_wages']:.2f}", f"${report_data['total_employee_contribution']:.2f}", f"${report_data['total_employer_contribution']:.2f}", f"${report_data['total_pf_amount']:.2f}", ''])
            
        elif report_type == 'esi':
            writer.writerow(['Employee ID', 'Name', 'ESI Number', 'Gross Salary', 'Employee Contribution', 'Employer Contribution', 'Total ESI', 'Filing Status'])
            for employee in report_data['employees']:
                writer.writerow([
                    employee['id'],
                    employee['name'],
                    employee['esi_number'],
                    f"${employee['gross_salary']:.2f}",
                    f"${employee['employee_contribution']:.2f}",
                    f"${employee['employer_contribution']:.2f}",
                    f"${employee['total_esi']:.2f}",
                    employee['filing_status']
                ])
            writer.writerow(['', '', 'Total', f"${report_data['total_gross_salary']:.2f}", f"${report_data['total_employee_contribution']:.2f}", f"${report_data['total_employer_contribution']:.2f}", f"${report_data['total_esi']:.2f}", ''])
            
        elif report_type == 'tds':
            writer.writerow(['Employee ID', 'Name', 'PAN Number', 'Taxable Income', 'TDS Deducted', 'Financial Year', 'Status'])
            for employee in report_data['employees']:
                writer.writerow([
                    employee['id'],
                    employee['name'],
                    employee['pan_number'],
                    f"${employee['taxable_income']:.2f}",
                    f"${employee['tds_deducted']:.2f}",
                    employee['financial_year'],
                    employee['filing_status']
                ])
            writer.writerow(['', '', 'Total', f"${report_data['total_taxable_income']:.2f}", f"${report_data['total_tds_deducted']:.2f}", '', ''])
            
        elif report_type == 'pt':
            writer.writerow(['Employee ID', 'Name', 'State', 'Gross Salary', 'PT Amount', 'Filing Status'])
            for employee in report_data['employees']:
                writer.writerow([
                    employee['id'],
                    employee['name'],
                    employee['state'],
                    f"${employee['gross_salary']:.2f}",
                    f"${employee['pt_amount']:.2f}",
                    employee['filing_status']
                ])
            writer.writerow(['', '', 'Total', f"${report_data['total_gross_salary']:.2f}", f"${report_data['total_pt_amount']:.2f}", ''])
            
        # Prepare response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report_{month}_{year}.csv'
        
        return response
    except Exception as e:
        app.logger.error(f"CSV generation failed: {str(e)}")
        return jsonify({'error': 'CSV generation failed', 'message': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
