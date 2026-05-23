import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.utils import secure_filename
from models.base import db
from models.models import Admin, Alumni, Student, Event, Webinar, JobPosting, ActivityLog, Notification, EventRegistration, WebinarRegistration
from routes.auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# File Upload Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Admin Dashboard
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Fetch statistics
    total_alumni = Alumni.query.count()
    total_students = Student.query.count()
    total_events = Event.query.count()
    total_webinars = Webinar.query.count()
    total_jobs = JobPosting.query.count()

    # Fetch pending approvals
    pending_alumni = Alumni.query.filter_by(is_approved=False).all()
    pending_students = Student.query.filter_by(is_approved=False).all()

    # Activity logs
    activity_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()

    return render_template(
        'admin/dashboard.html',
        total_alumni=total_alumni,
        total_students=total_students,
        total_events=total_events,
        total_webinars=total_webinars,
        total_jobs=total_jobs,
        pending_alumni=pending_alumni,
        pending_students=pending_students,
        activity_logs=activity_logs
    )

# Approve/Reject Alumni
@admin_bp.route('/approve/alumni/<int:user_id>', methods=['POST'])
@admin_required
def approve_alumni(user_id):
    alumni = Alumni.query.get_or_404(user_id)
    alumni.is_approved = True
    
    # Notify user
    notif = Notification(user_role='alumni', user_id=alumni.id, message="Your registration has been approved! You can now access your dashboard.")
    db.session.add(notif)
    
    # Log activity
    log = ActivityLog(action="Approved Alumni", details=f"Approved alumni: {alumni.name} ({alumni.email})")
    db.session.add(log)
    
    db.session.commit()
    flash(f"Approved alumni registration for {alumni.name}.", "success")
    referrer = request.referrer
    if referrer and ('/admin/users' in referrer or '/admin/dashboard' in referrer):
        return redirect(referrer)
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/reject/alumni/<int:user_id>', methods=['POST'])
@admin_required
def reject_alumni(user_id):
    alumni = Alumni.query.get_or_404(user_id)
    name = alumni.name
    email = alumni.email
    db.session.delete(alumni)
    
    # Log activity
    log = ActivityLog(action="Rejected Alumni", details=f"Rejected alumni registration: {name} ({email})")
    db.session.add(log)
    
    db.session.commit()
    flash(f"Rejected alumni registration for {name}.", "warning")
    referrer = request.referrer
    if referrer and ('/admin/users' in referrer or '/admin/dashboard' in referrer):
        return redirect(referrer)
    return redirect(url_for('admin.dashboard'))

# Approve/Reject Student
@admin_bp.route('/approve/student/<int:user_id>', methods=['POST'])
@admin_required
def approve_student(user_id):
    student = Student.query.get_or_404(user_id)
    student.is_approved = True
    
    # Notify user
    notif = Notification(user_role='student', user_id=student.id, message="Your registration has been approved! You can now access your dashboard.")
    db.session.add(notif)
    
    # Log activity
    log = ActivityLog(action="Approved Student", details=f"Approved student: {student.name} ({student.email})")
    db.session.add(log)
    
    db.session.commit()
    flash(f"Approved student registration for {student.name}.", "success")
    referrer = request.referrer
    if referrer and ('/admin/users' in referrer or '/admin/dashboard' in referrer):
        return redirect(referrer)
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/reject/student/<int:user_id>', methods=['POST'])
@admin_required
def reject_student(user_id):
    student = Student.query.get_or_404(user_id)
    name = student.name
    email = student.email
    db.session.delete(student)
    
    # Log activity
    log = ActivityLog(action="Rejected Student", details=f"Rejected student registration: {name} ({email})")
    db.session.add(log)
    
    db.session.commit()
    flash(f"Rejected student registration for {name}.", "warning")
    referrer = request.referrer
    if referrer and ('/admin/users' in referrer or '/admin/dashboard' in referrer):
        return redirect(referrer)
    return redirect(url_for('admin.dashboard'))

# Manage Users Page
@admin_bp.route('/users')
@admin_required
def manage_users():
    search_query = request.args.get('query', '').strip()
    
    if search_query:
        alumni_list = Alumni.query.filter(Alumni.name.like(f"%{search_query}%") | Alumni.email.like(f"%{search_query}%")).all()
        student_list = Student.query.filter(Student.name.like(f"%{search_query}%") | Student.email.like(f"%{search_query}%")).all()
    else:
        alumni_list = Alumni.query.all()
        student_list = Student.query.all()
        
    return render_template('admin/users.html', alumni_list=alumni_list, student_list=student_list, search_query=search_query)

# Delete Users
@admin_bp.route('/delete/alumni/<int:user_id>', methods=['POST'])
@admin_required
def delete_alumni(user_id):
    alumni = Alumni.query.get_or_404(user_id)
    name = alumni.name
    db.session.delete(alumni)
    
    log = ActivityLog(action="Deleted Alumni", details=f"Deleted alumni account: {name}")
    db.session.add(log)
    
    db.session.commit()
    flash(f"Alumni account for {name} has been deleted.", "success")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/delete/student/<int:user_id>', methods=['POST'])
@admin_required
def delete_student(user_id):
    student = Student.query.get_or_404(user_id)
    name = student.name
    db.session.delete(student)
    
    log = ActivityLog(action="Deleted Student", details=f"Deleted student account: {name}")
    db.session.add(log)
    
    db.session.commit()
    flash(f"Student account for {name} has been deleted.", "success")
    return redirect(url_for('admin.manage_users'))

# Manage Events
@admin_bp.route('/events', methods=['GET', 'POST'])
@admin_required
def manage_events():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        date_str = request.form.get('event_date')
        location = request.form.get('location', '').strip()

        from datetime import datetime
        try:
            event_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid date and time format.", "danger")
            return redirect(url_for('admin.manage_events'))

        new_event = Event(
            title=title,
            description=description,
            event_date=event_date,
            location=location,
            created_by=session['user_id']
        )
        db.session.add(new_event)
        
        log = ActivityLog(action="Created Event", details=f"Admin created event: {title}")
        db.session.add(log)
        
        # Notify all students
        students = Student.query.filter_by(is_approved=True).all()
        for student in students:
            notif = Notification(user_role='student', user_id=student.id, message=f"New event announcement: {title}")
            db.session.add(notif)
            
        db.session.commit()
        flash(f"Event '{title}' created successfully!", "success")
        return redirect(url_for('admin.manage_events'))

    events = Event.query.order_by(Event.event_date.asc()).all()
    # Fetch registrations count per event
    reg_counts = {}
    for event in events:
        reg_counts[event.id] = EventRegistration.query.filter_by(event_id=event.id).count()

    return render_template('admin/events.html', events=events, reg_counts=reg_counts)

@admin_bp.route('/delete/event/<int:event_id>', methods=['POST'])
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    title = event.title
    db.session.delete(event)
    
    log = ActivityLog(action="Deleted Event", details=f"Admin deleted event: {title}")
    db.session.add(log)
    
    db.session.commit()
    flash(f"Event '{title}' has been deleted.", "success")
    return redirect(url_for('admin.manage_events'))

# Manage Webinars
@admin_bp.route('/webinars')
@admin_required
def manage_webinars():
    webinars = Webinar.query.order_by(Webinar.webinar_date.asc()).all()
    reg_counts = {}
    for web in webinars:
        reg_counts[web.id] = WebinarRegistration.query.filter_by(webinar_id=web.id).count()
        
    return render_template('admin/webinars.html', webinars=webinars, reg_counts=reg_counts)

@admin_bp.route('/delete/webinar/<int:webinar_id>', methods=['POST'])
@admin_required
def delete_webinar(webinar_id):
    webinar = Webinar.query.get_or_404(webinar_id)
    title = webinar.title
    db.session.delete(webinar)
    
    log = ActivityLog(action="Deleted Webinar", details=f"Admin deleted webinar: {title}")
    db.session.add(log)
    
    db.session.commit()
    flash(f"Webinar '{title}' deleted by administrator.", "success")
    return redirect(url_for('admin.manage_webinars'))

# Manage Jobs
@admin_bp.route('/jobs')
@admin_required
def manage_jobs():
    jobs = JobPosting.query.order_by(JobPosting.created_at.desc()).all()
    return render_template('admin/jobs.html', jobs=jobs)

@admin_bp.route('/delete/job/<int:job_id>', methods=['POST'])
@admin_required
def delete_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    title = job.title
    db.session.delete(job)
    
    log = ActivityLog(action="Deleted Job Posting", details=f"Admin deleted job posting: {title} ({job.company})")
    db.session.add(log)
    
    db.session.commit()
    flash(f"Job posting '{title}' removed.", "success")
    return redirect(url_for('admin.manage_jobs'))

# Reports Page
@admin_bp.route('/reports')
@admin_required
def reports():
    # Collect summary data for charts
    alumni_approved = Alumni.query.filter_by(is_approved=True).count()
    alumni_pending = Alumni.query.filter_by(is_approved=False).count()
    student_approved = Student.query.filter_by(is_approved=True).count()
    student_pending = Student.query.filter_by(is_approved=False).count()
    
    events_count = Event.query.count()
    webinars_count = Webinar.query.count()
    jobs_count = JobPosting.query.count()
    
    # Simple report details
    return render_template(
        'admin/reports.html',
        alumni_approved=alumni_approved,
        alumni_pending=alumni_pending,
        student_approved=student_approved,
        student_pending=student_pending,
        events_count=events_count,
        webinars_count=webinars_count,
        jobs_count=jobs_count
    )

# Send Announcement
@admin_bp.route('/announcements', methods=['POST'])
@admin_required
def send_announcement():
    message = request.form.get('announcement', '').strip()
    if not message:
        flash("Announcement message cannot be empty.", "danger")
        return redirect(url_for('admin.dashboard'))

    # Send notifications to all students & alumni
    students = Student.query.filter_by(is_approved=True).all()
    alumni = Alumni.query.filter_by(is_approved=True).all()

    for student in students:
        notif = Notification(user_role='student', user_id=student.id, message=f"Admin Announcement: {message}")
        db.session.add(notif)

    for alum in alumni:
        notif = Notification(user_role='alumni', user_id=alum.id, message=f"Admin Announcement: {message}")
        db.session.add(notif)

    log = ActivityLog(action="Sent Announcement", details=f"Broadcast message: {message[:100]}...")
    db.session.add(log)
    db.session.commit()

    flash("Global announcement broadcasted successfully!", "success")
    return redirect(url_for('admin.dashboard'))

# Admin Profile Edit
@admin_bp.route('/profile', methods=['GET', 'POST'])
@admin_required
def profile():
    admin = Admin.query.get(session['user_id'])
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        
        # Check duplicate emails
        existing = Admin.query.filter(Admin.email == email, Admin.id != admin.id).first()
        if existing or Alumni.query.filter_by(email=email).first() or Student.query.filter_by(email=email).first():
            flash("This email is already in use by another user.", "danger")
            return redirect(url_for('admin.profile'))
            
        admin.name = name
        admin.email = email

        # Profile Picture Upload
        file = request.files.get('profile_pic')
        if file and file.filename != '' and allowed_file(file.filename):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = f"admin_{admin.id}_{secure_filename(file.filename)}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            admin.profile_pic = filename
            session['profile_pic'] = filename
            
        db.session.commit()
        session['name'] = admin.name
        flash("Profile updated successfully!", "success")
        return redirect(url_for('admin.profile'))

    return render_template('admin/profile.html', admin=admin)
