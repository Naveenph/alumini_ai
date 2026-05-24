import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from functools import wraps
import uuid
import random
from models.base import db, mail
from flask_mail import Message
from models.models import Admin, Alumni, Student, ActivityLog

def send_verification_email(email, name, token, otp):
    try:
        msg = Message('Verify your Alumni Network Account', recipients=[email])
        verify_link = url_for('auth.verify_email', token=token, _external=True)
        msg.body = f"Hello {name},\n\nYour OTP for email verification is: {otp}\n\nYou can also click the link below to verify your account:\n{verify_link}\n\nThank you!"
        mail.send(msg)
    except Exception as e:
        print("Email sending failed:", e)

auth_bp = Blueprint('auth', __name__)

# Authorization Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'role' not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for('auth.login_view'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash("Unauthorized access. Admin privilege required.", "danger")
            return redirect(url_for('auth.login_view'))
        # Check existence
        admin = Admin.query.get(session['user_id'])
        if not admin:
            session.clear()
            flash("Administrator account not found. Please log in again.", "danger")
            return redirect(url_for('auth.login_view'))
        return f(*args, **kwargs)
    return decorated_function

def alumni_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'alumni':
            flash("Unauthorized access. Alumni login required.", "danger")
            return redirect(url_for('auth.login_view'))
        # Check approval
        user = Alumni.query.get(session['user_id'])
        if not user or not user.is_approved:
            session.clear()
            flash("Your alumni account is pending admin approval.", "warning")
            return redirect(url_for('auth.login_view'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'student':
            flash("Unauthorized access. Student login required.", "danger")
            return redirect(url_for('auth.login_view'))
        # Check approval
        user = Student.query.get(session['user_id'])
        if not user or not user.is_approved:
            session.clear()
            flash("Your student account is pending admin approval.", "warning")
            return redirect(url_for('auth.login_view'))
        return f(*args, **kwargs)
    return decorated_function

# Unified Page View for Login / Register
@auth_bp.route('/login')
def login_view():
    if 'user_id' in session:
        role = session.get('role')
        return redirect(url_for(f'{role}.dashboard'))
    return render_template('login.html')

@auth_bp.route('/register')
def register_view():
    if 'user_id' in session:
        role = session.get('role')
        return redirect(url_for(f'{role}.dashboard'))
    return render_template('register.html')

# 1. Admin Auth Handlers
@auth_bp.route('/login/admin', methods=['POST'])
def login_admin():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    admin = Admin.query.filter_by(email=email).first()
    if admin and admin.check_password(password):
        session.clear()
        session['user_id'] = admin.id
        session['role'] = 'admin'
        session['name'] = admin.name
        session['profile_pic'] = admin.profile_pic
        flash(f"Welcome back, Admin {admin.name}!", "success")
        return redirect(url_for('admin.dashboard'))
    
    flash("Invalid admin email or password.", "danger")
    return redirect(url_for('auth.login_view', role='admin'))

@auth_bp.route('/register/admin', methods=['POST'])
def register_admin():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    secret_code = request.form.get('secret_code', '').strip()
    
    required_code = os.getenv("ADMIN_SECRET_CODE", "ADMIN_REGISTER_2026")
    if secret_code != required_code:
        flash("Invalid Admin Secret Code. You cannot register as an administrator.", "danger")
        return redirect(url_for('auth.register_view', role='admin'))
        
    if Admin.query.filter_by(email=email).first() or Alumni.query.filter_by(email=email).first() or Student.query.filter_by(email=email).first():
        flash("An account with this email already exists.", "danger")
        return redirect(url_for('auth.register_view', role='admin'))

    new_admin = Admin(name=name, email=email)
    new_admin.set_password(password)
    db.session.add(new_admin)
    db.session.commit()
    
    # Log activity
    log = ActivityLog(action="Admin Registration", details=f"New admin registered: {name} ({email})")
    db.session.add(log)
    db.session.commit()
    
    flash("Admin registration successful! You can now log in.", "success")
    return redirect(url_for('auth.login_view', role='admin'))

# 2. Alumni Auth Handlers
@auth_bp.route('/login/alumni', methods=['POST'])
def login_alumni():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    alumni = Alumni.query.filter_by(email=email).first()
    if alumni and alumni.check_password(password):
        if not alumni.is_email_verified:
            flash("Please verify your email address first.", "warning")
            return redirect(url_for('auth.verify_otp_view', email=email, role='alumni'))
            
        if not alumni.is_approved:
            flash("Your registration is pending approval by the Admin.", "warning")
            return redirect(url_for('auth.login_view'))
            
        session.clear()
        session['user_id'] = alumni.id
        session['role'] = 'alumni'
        session['name'] = alumni.name
        session['profile_pic'] = alumni.profile_pic
        flash(f"Welcome, {alumni.name}!", "success")
        return redirect(url_for('alumni.dashboard'))
        
    flash("Invalid alumni email or password.", "danger")
    return redirect(url_for('auth.login_view'))

@auth_bp.route('/register/alumni', methods=['POST'])
def register_alumni():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    graduation_year = request.form.get('graduation_year')
    company = request.form.get('company', '').strip()
    designation = request.form.get('designation', '').strip()
    skills = request.form.get('skills', '').strip()
    domain = request.form.get('domain', '').strip()

    if not name or not email or not password or not graduation_year:
        flash("Please fill in all required fields.", "danger")
        return redirect(url_for('auth.register_view'))
        
    allowed_domain = os.getenv("ALLOWED_EMAIL_DOMAIN", "")
    if allowed_domain and not email.endswith(allowed_domain):
        flash(f"Only emails ending with {allowed_domain} are allowed.", "danger")
        return redirect(url_for('auth.register_view'))

    if Admin.query.filter_by(email=email).first() or Alumni.query.filter_by(email=email).first() or Student.query.filter_by(email=email).first():
        flash("An account with this email already exists.", "danger")
        return redirect(url_for('auth.register_view'))

    new_alumni = Alumni(
        name=name,
        email=email,
        graduation_year=int(graduation_year),
        company=company if company else None,
        designation=designation if designation else None,
        skills=skills if skills else None,
        domain=domain if domain else None,
        is_approved=False
    )
    new_alumni.email_verification_token = str(uuid.uuid4())
    new_alumni.email_verification_otp = str(random.randint(100000, 999999))
    new_alumni.set_password(password)
    db.session.add(new_alumni)
    db.session.commit()
    
    send_verification_email(email, name, new_alumni.email_verification_token, new_alumni.email_verification_otp)

    flash("Registration successful! Please check your email for the verification code.", "info")
    return redirect(url_for('auth.verify_otp_view', email=email, role='alumni'))

# 3. Student Auth Handlers
@auth_bp.route('/login/student', methods=['POST'])
def login_student():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    student = Student.query.filter_by(email=email).first()
    if student and student.check_password(password):
        if not student.is_email_verified:
            flash("Please verify your email address first.", "warning")
            return redirect(url_for('auth.verify_otp_view', email=email, role='student'))
            
        if not student.is_approved:
            flash("Your registration is pending approval by the Admin.", "warning")
            return redirect(url_for('auth.login_view'))

        session.clear()
        session['user_id'] = student.id
        session['role'] = 'student'
        session['name'] = student.name
        session['profile_pic'] = student.profile_pic
        flash(f"Welcome, {student.name}!", "success")
        return redirect(url_for('student.dashboard'))

    flash("Invalid student email or password.", "danger")
    return redirect(url_for('auth.login_view'))

@auth_bp.route('/register/student', methods=['POST'])
def register_student():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    graduation_year = request.form.get('graduation_year')
    skills = request.form.get('skills', '').strip()
    domain = request.form.get('domain', '').strip()

    if not name or not email or not password or not graduation_year:
        flash("Please fill in all required fields.", "danger")
        return redirect(url_for('auth.register_view'))
        
    allowed_domain = os.getenv("ALLOWED_EMAIL_DOMAIN", "")
    if allowed_domain and not email.endswith(allowed_domain):
        flash(f"Only emails ending with {allowed_domain} are allowed.", "danger")
        return redirect(url_for('auth.register_view'))

    if Admin.query.filter_by(email=email).first() or Alumni.query.filter_by(email=email).first() or Student.query.filter_by(email=email).first():
        flash("An account with this email already exists.", "danger")
        return redirect(url_for('auth.register_view'))

    new_student = Student(
        name=name,
        email=email,
        graduation_year=int(graduation_year),
        skills=skills if skills else None,
        domain=domain if domain else None,
        is_approved=False
    )
    new_student.email_verification_token = str(uuid.uuid4())
    new_student.email_verification_otp = str(random.randint(100000, 999999))
    new_student.set_password(password)
    db.session.add(new_student)
    db.session.commit()
    
    send_verification_email(email, name, new_student.email_verification_token, new_student.email_verification_otp)

    flash("Registration successful! Please check your email for the verification code.", "info")
    return redirect(url_for('auth.verify_otp_view', email=email, role='student'))

# Forgot Password (Mock verification & reset)
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        new_password = request.form.get('password', '').strip()
        role = request.form.get('role', '')

        if not email or not new_password or not role:
            flash("Please fill in all fields.", "danger")
            return render_template('forgot_password.html')

        user = None
        if role == 'admin':
            user = Admin.query.filter_by(email=email).first()
        elif role == 'alumni':
            user = Alumni.query.filter_by(email=email).first()
        elif role == 'student':
            user = Student.query.filter_by(email=email).first()

        if user:
            user.set_password(new_password)
            db.session.commit()
            flash("Password updated successfully! You can now log in.", "success")
            return redirect(url_for('auth.login_view'))
        else:
            flash("Email not found in our database.", "danger")
            
    return render_template('forgot_password.html')

# Email Verification Endpoints
@auth_bp.route('/verify/<token>')
def verify_email(token):
    # Check alumni
    alumni = Alumni.query.filter_by(email_verification_token=token).first()
    if alumni:
        alumni.is_email_verified = True
        alumni.email_verification_token = None
        alumni.email_verification_otp = None
        db.session.commit()
        flash("Email verified successfully! You can now log in.", "success")
        return redirect(url_for('auth.login_view'))
        
    student = Student.query.filter_by(email_verification_token=token).first()
    if student:
        student.is_email_verified = True
        student.email_verification_token = None
        student.email_verification_otp = None
        db.session.commit()
        flash("Email verified successfully! You can now log in.", "success")
        return redirect(url_for('auth.login_view'))

    flash("Invalid or expired verification link.", "danger")
    return redirect(url_for('auth.login_view'))

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp_view():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        otp = request.form.get('otp', '').strip()
        role = request.form.get('role', '')

        if not email or not otp or not role:
            flash("Please provide all required fields.", "danger")
            return redirect(url_for('auth.verify_otp_view', email=email, role=role))

        user = None
        if role == 'alumni':
            user = Alumni.query.filter_by(email=email).first()
        elif role == 'student':
            user = Student.query.filter_by(email=email).first()

        if user and user.email_verification_otp == otp:
            user.is_email_verified = True
            user.email_verification_token = None
            user.email_verification_otp = None
            db.session.commit()
            flash("Email verified successfully! You can now log in.", "success")
            return redirect(url_for('auth.login_view'))
        else:
            flash("Invalid OTP.", "danger")
            return redirect(url_for('auth.verify_otp_view', email=email, role=role))

    email = request.args.get('email', '')
    role = request.args.get('role', '')
    
    console_otp = ""
    if email and role:
        user = Alumni.query.filter_by(email=email).first() if role == 'alumni' else Student.query.filter_by(email=email).first()
        if user and user.email_verification_otp:
            console_otp = user.email_verification_otp
            
    return render_template('verify_otp.html', email=email, role=role, console_otp=console_otp)

# Logout
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('home'))
