from functools import wraps
from flask import session, redirect, url_for, flash

# Authentication decorators
def employee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def hr_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'danger')
            return redirect(url_for('login'))
        if session.get('role') != 'hr':
            flash('You do not have permission to access this page', 'danger')
            return redirect(url_for('employee_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Helper functions for payroll calculation
def calculate_days_in_month(month, year):
    """Calculate the number of days in a given month/year"""
    import calendar
    return calendar.monthrange(year, month)[1]

def calculate_working_days(month, year):
    """Calculate working days in a month (excluding weekends)"""
    import calendar
    cal = calendar.monthcalendar(year, month)
    return sum(1 for week in cal for day in range(5) if week[day] != 0)

def format_currency(amount):
    """Format amount as currency"""
    return "${:,.2f}".format(amount)

def get_month_name(month_number):
    """Convert month number to name"""
    import calendar
    return calendar.month_name[month_number]
