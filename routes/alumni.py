import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.utils import secure_filename
from models.base import db
from models.models import Alumni, Student, JobPosting, Webinar, MentorshipRequest, WebinarRegistration, Notification
from routes.auth import alumni_required

alumni_bp = Blueprint('alumni', __name__, url_prefix='/alumni')

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Alumni Dashboard
@alumni_bp.route('/dashboard')
@alumni_required
def dashboard():
    alumni = Alumni.query.get(session['user_id'])
    
    # Statistics
    total_jobs = JobPosting.query.filter_by(posted_by_alumni_id=alumni.id).count()
    total_webinars = Webinar.query.filter_by(speaker_id=alumni.id).count()
    total_connections = MentorshipRequest.query.filter_by(alumni_id=alumni.id, status='accepted').count()
    
    # Pending requests from students
    pending_requests = MentorshipRequest.query.filter_by(alumni_id=alumni.id, status='pending').all()
    
    # Recent system announcements from admin (via notifications)
    announcements = Notification.query.filter_by(user_role='alumni', user_id=alumni.id).order_by(Notification.created_at.desc()).limit(5).all()

    # Mark notifications as read
    for ann in announcements:
        ann.is_read = True
    db.session.commit()

    return render_template(
        'alumni/dashboard.html',
        alumni=alumni,
        total_jobs=total_jobs,
        total_webinars=total_webinars,
        total_connections=total_connections,
        pending_requests=pending_requests,
        announcements=announcements
    )

# Connection Request Moderation (Approve/Reject Student Connects)
@alumni_bp.route('/request/<int:req_id>/<string:action>', methods=['POST'])
@alumni_required
def handle_request(req_id, action):
    req = MentorshipRequest.query.get_or_404(req_id)
    if req.alumni_id != session['user_id']:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('alumni.dashboard'))
        
    if action == 'approve':
        req.status = 'accepted'
        # Notify student
        notif = Notification(user_role='student', user_id=req.student_id, message=f"Alumni {req.alumni.name} accepted your mentorship request!")
        db.session.add(notif)
        flash("Mentorship request approved!", "success")
    elif action == 'reject':
        req.status = 'rejected'
        db.session.delete(req) # Delete request if rejected
        flash("Mentorship request declined.", "warning")
        
    db.session.commit()
    return redirect(url_for('alumni.dashboard'))

# Alumni Edit Profile
@alumni_bp.route('/profile', methods=['GET', 'POST'])
@alumni_required
def profile():
    alumni = Alumni.query.get(session['user_id'])
    if request.method == 'POST':
        alumni.name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        
        # Check email duplicates
        existing = Alumni.query.filter(Alumni.email == email, Alumni.id != alumni.id).first()
        if existing or Student.query.filter_by(email=email).first():
            flash("This email is already in use by another user.", "danger")
            return redirect(url_for('alumni.profile'))

        alumni.email = email
        alumni.company = request.form.get('company', '').strip()
        alumni.designation = request.form.get('designation', '').strip()
        alumni.skills = request.form.get('skills', '').strip()
        alumni.domain = request.form.get('domain', '').strip()
        alumni.graduation_year = int(request.form.get('graduation_year', alumni.graduation_year))
        alumni.linkedin = request.form.get('linkedin', '').strip()

        # Handle file upload for profile pic
        file = request.files.get('profile_pic')
        if file and file.filename != '' and allowed_file(file.filename):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = f"alumni_{alumni.id}_{secure_filename(file.filename)}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            alumni.profile_pic = filename
            session['profile_pic'] = filename

        db.session.commit()
        session['name'] = alumni.name
        flash("Profile updated successfully!", "success")
        return redirect(url_for('alumni.profile'))

    return render_template('alumni/profile.html', alumni=alumni)

# Alumni Job Listings
@alumni_bp.route('/jobs', methods=['GET', 'POST'])
@alumni_required
def jobs():
    alumni_id = session['user_id']
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        company = request.form.get('company', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        requirements = request.form.get('requirements', '').strip() # skills comma-separated

        new_job = JobPosting(
            title=title,
            company=company,
            location=location,
            description=description,
            requirements=requirements,
            posted_by_alumni_id=alumni_id
        )
        db.session.add(new_job)
        
        # Create notifications for students matching these skills or interest
        # Simple loop: notify students who have overlapping skills
        students = Student.query.filter_by(is_approved=True).all()
        job_skills = set([s.lower().strip() for s in requirements.split(',') if s.strip()])
        for student in students:
            if student.skills:
                student_skills = set([s.lower().strip() for s in student.skills.split(',') if s.strip()])
                if job_skills.intersection(student_skills):
                    notif = Notification(
                        user_role='student',
                        user_id=student.id,
                        message=f"Job Recommendation: New job '{title}' matching your skills posted by {company}."
                    )
                    db.session.add(notif)
                    
        db.session.commit()
        flash(f"Job posting '{title}' added successfully!", "success")
        return redirect(url_for('alumni.jobs'))

    my_jobs = JobPosting.query.filter_by(posted_by_alumni_id=alumni_id).order_by(JobPosting.created_at.desc()).all()
    return render_template('alumni/jobs.html', jobs=my_jobs)

@alumni_bp.route('/jobs/delete/<int:job_id>', methods=['POST'])
@alumni_required
def delete_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    if job.posted_by_alumni_id != session['user_id']:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('alumni.jobs'))

    db.session.delete(job)
    db.session.commit()
    flash("Job posting deleted.", "success")
    return redirect(url_for('alumni.jobs'))

# Alumni Webinars
@alumni_bp.route('/webinars', methods=['GET', 'POST'])
@alumni_required
def webinars():
    alumni_id = session['user_id']
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        date_str = request.form.get('webinar_date')
        link = request.form.get('link', '').strip()

        from datetime import datetime
        try:
            webinar_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid date/time format.", "danger")
            return redirect(url_for('alumni.webinars'))

        new_webinar = Webinar(
            title=title,
            description=description,
            webinar_date=webinar_date,
            link=link,
            speaker_id=alumni_id
        )
        db.session.add(new_webinar)
        
        # Notify all students
        students = Student.query.filter_by(is_approved=True).all()
        for student in students:
            notif = Notification(user_role='student', user_id=student.id, message=f"Webinar Invitation: '{title}' hosted by alumnus {session['name']}")
            db.session.add(notif)
            
        db.session.commit()
        flash(f"Webinar '{title}' scheduled successfully!", "success")
        return redirect(url_for('alumni.webinars'))

    my_webinars = Webinar.query.filter_by(speaker_id=alumni_id).order_by(Webinar.webinar_date.asc()).all()
    # Registrants list count
    reg_counts = {}
    for web in my_webinars:
        reg_counts[web.id] = WebinarRegistration.query.filter_by(webinar_id=web.id).count()
        
    return render_template('alumni/webinars.html', webinars=my_webinars, reg_counts=reg_counts)

# View Students registered for a webinar
@alumni_bp.route('/webinars/<int:webinar_id>/registrants')
@alumni_required
def webinar_registrants(webinar_id):
    webinar = Webinar.query.get_or_404(webinar_id)
    if webinar.speaker_id != session['user_id']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('alumni.webinars'))

    registrations = WebinarRegistration.query.filter_by(webinar_id=webinar_id).all()
    return render_template('alumni/webinar_registrants.html', webinar=webinar, registrations=registrations)

# Messaging page
@alumni_bp.route('/messages')
@alumni_required
def messages():
    # Fetch all students with active connections
    connections = MentorshipRequest.query.filter_by(alumni_id=session['user_id'], status='accepted').all()
    active_chat_student_id = request.args.get('chat_with')
    
    active_student = None
    if active_chat_student_id:
        active_student = Student.query.get(active_chat_student_id)
        
    return render_template('alumni/messages.html', connections=connections, active_student=active_student)
