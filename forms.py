from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, FloatField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('employee', 'Employee'), ('hr', 'HR Admin')])

class EmployeeProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    address = TextAreaField('Address', validators=[Optional()])
    phone = StringField('Phone Number', validators=[Optional()])
    emergency_contact = StringField('Emergency Contact', validators=[Optional()])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    department = StringField('Department', validators=[DataRequired()])
    designation = StringField('Designation', validators=[DataRequired()])

class AttendanceForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('wfh', 'Work From Home')
    ], validators=[DataRequired()])
    note = TextAreaField('Note', validators=[Optional()])

class LeaveApplicationForm(FlaskForm):
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    leave_type = SelectField('Leave Type', choices=[
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('unpaid', 'Unpaid Leave')
    ], validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[DataRequired()])

class InquiryForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])

class AddEmployeeForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    department = StringField('Department', validators=[DataRequired()])
    designation = StringField('Designation', validators=[DataRequired()])
    salary = FloatField('Basic Salary', validators=[DataRequired()])

class EditEmployeeForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    designation = StringField('Designation', validators=[DataRequired()])
    salary = FloatField('Basic Salary', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], validators=[DataRequired()])
