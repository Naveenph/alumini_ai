import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.utils import secure_filename
from models.base import db
from models.models import Student, Alumni, JobPosting, Event, Webinar, EventRegistration, WebinarRegistration, MentorshipRequest, Notification, AIRecommendation, FlashcardImage
from routes.auth import student_required

student_bp = Blueprint('student', __name__, url_prefix='/student')

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Rule-Based AI Recommendations (Python-based simple logical conditions, no ML)
def get_ai_recommendations(student, limit=5, include_connected=False):
    """Enhanced AI recommendation engine scoring alumni by domain, skills, location, and grad year."""
    recommended_alumni = []
    recommended_jobs = []

    # Prepare student signals
    student_skills = [s.lower().strip() for s in (student.skills or '').split(',') if s.strip()]
    student_domain = (student.domain or '').lower().strip()
    student_location = (student.job_location or '').lower().strip()

    # 1. Recommend Mentors (Alumni)
    # Scoring rules:
    #   A. Domain match         → +40 pts
    #   B. Skill overlap        → +15 pts/skill (max 45)
    #   C. Location match       → +25 pts (alumni company location ~= student preferred location)
    #   D. Grad year proximity  → +15 pts (within 5 years)
    all_alumni = Alumni.query.filter_by(is_approved=True).all()
    alumni_scores = []

    for alum in all_alumni:
        # Optionally skip already connected/pending alumni
        if not include_connected:
            existing_conn = MentorshipRequest.query.filter_by(student_id=student.id, alumni_id=alum.id).first()
            if existing_conn:
                continue

        score = 0
        reasons = []

        # Rule A: Domain match
        alum_domain = (alum.domain or '').lower().strip()
        if student_domain and alum_domain and alum_domain == student_domain:
            score += 40
            reasons.append(f"Domain match ({alum.domain})")

        # Rule B: Skill matches
        alum_skills = [s.lower().strip() for s in (alum.skills or '').split(',') if s.strip()]
        skill_matches = set(student_skills).intersection(set(alum_skills))
        if skill_matches:
            points = len(skill_matches) * 15
            score += min(points, 45)
            reasons.append(f"Matching skills: {', '.join(list(skill_matches)[:3])}")

        # Rule C: Job location preference match (alumni's company location)
        alum_company = (alum.company or '').lower().strip()
        alum_designation = (alum.designation or '').lower().strip()
        # We don't have alumni location in model, so match on company name keywords or designation
        # Match student preferred location against alumni domain/company description
        if student_location:
            # Try partial match on company or designation fields
            if (student_location in alum_company or 
                student_location in alum_domain or
                student_location in alum_designation):
                score += 25
                reasons.append(f"Location match ({student.job_location})")

        # Rule D: Grad Year proximity (within 5 years)
        if abs(alum.graduation_year - student.graduation_year) <= 5:
            score += 15
            reasons.append("Recent graduate (near your year)")

        if score > 0:
            alumni_scores.append((alum, score, ", ".join(reasons)))

    # Sort alumni by score descending
    alumni_scores.sort(key=lambda x: x[1], reverse=True)
    recommended_alumni = [
        {"alumni": alum, "score": score, "reason": reason}
        for alum, score, reason in alumni_scores[:limit]
    ]

    # 2. Recommend Jobs
    # Rules: skill overlap, domain keyword, location preference
    all_jobs = JobPosting.query.order_by(JobPosting.created_at.desc()).all()
    job_scores = []

    for job in all_jobs:
        score = 0
        reasons = []

        # Rule A: Skills requirement matches student skills
        job_reqs = [r.lower().strip() for r in (job.requirements or '').split(',') if r.strip()]
        req_matches = set(student_skills).intersection(set(job_reqs))
        if req_matches:
            points = len(req_matches) * 20
            score += points
            reasons.append(f"Skills match: {', '.join(list(req_matches)[:3])}")

        # Rule B: Domain interest matches job title or description
        if student_domain and (student_domain in job.title.lower() or student_domain in job.description.lower()):
            score += 20
            reasons.append(f"Matches domain interest ({student.domain})")

        # Rule C: Location preference matches job location
        if student_location and (student_location in job.location.lower()):
            score += 20
            reasons.append(f"Job in preferred location ({job.location})")

        if score > 0:
            job_scores.append((job, score, ", ".join(reasons)))

    # Sort jobs by score descending
    job_scores.sort(key=lambda x: x[1], reverse=True)
    recommended_jobs = [
        {"job": job, "score": score, "reason": reason}
        for job, score, reason in job_scores[:limit]
    ]

    return recommended_alumni, recommended_jobs


# Student Dashboard
@student_bp.route('/dashboard')
@student_required
def dashboard():
    student = Student.query.get(session['user_id'])
    
    # Counts
    events_count = EventRegistration.query.filter_by(student_id=student.id).count()
    webinars_count = WebinarRegistration.query.filter_by(student_id=student.id).count()
    connections_count = MentorshipRequest.query.filter_by(student_id=student.id, status='accepted').count()
    
    # AI recommendations
    rec_alumni, rec_jobs = get_ai_recommendations(student)
    
    # Notifications/Announcements
    notifications = Notification.query.filter_by(user_role='student', user_id=student.id).order_by(Notification.created_at.desc()).limit(8).all()
    
    # Mark read
    for notif in notifications:
        notif.is_read = True
    db.session.commit()
    
    # Flashcards
    flashcards = FlashcardImage.query.order_by(FlashcardImage.created_at.desc()).all()

    return render_template(
        'student/dashboard.html',
        student=student,
        events_count=events_count,
        webinars_count=webinars_count,
        connections_count=connections_count,
        rec_alumni=rec_alumni,
        rec_jobs=rec_jobs,
        notifications=notifications,
        flashcards=flashcards
    )

# Student Profile Edit
@student_bp.route('/profile', methods=['GET', 'POST'])
@student_required
def profile():
    student = Student.query.get(session['user_id'])
    if request.method == 'POST':
        student.name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()

        # Check email duplicates
        existing = Student.query.filter(Student.email == email, Student.id != student.id).first()
        if existing or Alumni.query.filter_by(email=email).first():
            flash("This email is already in use by another user.", "danger")
            return redirect(url_for('student.profile'))

        student.email = email
        student.skills = request.form.get('skills', '').strip()
        student.domain = request.form.get('domain', '').strip()
        student.job_location = request.form.get('job_location', '').strip()
        student.graduation_year = int(request.form.get('graduation_year', student.graduation_year))

        # Handle file upload for profile pic
        file = request.files.get('profile_pic')
        if file and file.filename != '' and allowed_file(file.filename):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = f"student_{student.id}_{secure_filename(file.filename)}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            student.profile_pic = filename
            session['profile_pic'] = filename

        db.session.commit()
        session['name'] = student.name
        flash("Profile updated successfully!", "success")
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html', student=student)

# Alumni Search
@student_bp.route('/search')
@student_required
def search():
    query = request.args.get('query', '').strip()
    company = request.args.get('company', '').strip()
    skills = request.args.get('skills', '').strip()
    domain = request.args.get('domain', '').strip()
    year = request.args.get('graduation_year', '').strip()

    alumni_query = Alumni.query.filter_by(is_approved=True)

    if query:
        alumni_query = alumni_query.filter(Alumni.name.like(f"%{query}%") | Alumni.email.like(f"%{query}%"))
    if company:
        alumni_query = alumni_query.filter(Alumni.company.like(f"%{company}%"))
    if skills:
        alumni_query = alumni_query.filter(Alumni.skills.like(f"%{skills}%"))
    if domain:
        alumni_query = alumni_query.filter(Alumni.domain.like(f"%{domain}%"))
    if year:
        alumni_query = alumni_query.filter(Alumni.graduation_year == int(year))

    alumni_list = alumni_query.all()
    
    # Check pending/active connections
    student_id = session['user_id']
    connections = {c.alumni_id: c.status for c in MentorshipRequest.query.filter_by(student_id=student_id).all()}

    return render_template('student/search.html', alumni_list=alumni_list, connections=connections)

# Send Mentorship Request
@student_bp.route('/connect/<int:alumni_id>', methods=['POST'])
@student_required
def connect(alumni_id):
    student_id = session['user_id']
    existing = MentorshipRequest.query.filter_by(student_id=student_id, alumni_id=alumni_id).first()
    
    if existing:
        flash("A connection request is already pending or established.", "warning")
        return redirect(url_for('student.search'))

    new_request = MentorshipRequest(student_id=student_id, alumni_id=alumni_id, status='pending')
    db.session.add(new_request)
    
    # Notify Alumni
    alumni = Alumni.query.get(alumni_id)
    notif = Notification(user_role='alumni', user_id=alumni_id, message=f"Student {session['name']} has sent you a mentorship connection request!")
    db.session.add(notif)
    
    db.session.commit()
    flash("Mentorship request sent successfully!", "success")
    return redirect(url_for('student.search'))

# Mentorship status page
@student_bp.route('/mentorship')
@student_required
def mentorship():
    student_id = session['user_id']
    requests_sent = MentorshipRequest.query.filter_by(student_id=student_id).all()
    return render_template('student/mentorship.html', requests_sent=requests_sent)

# Events & Webinars Page
@student_bp.route('/events')
@student_required
def events():
    student_id = session['user_id']
    
    # Fetch events and webinars
    events_list = Event.query.order_by(Event.event_date.asc()).all()
    webinars_list = Webinar.query.order_by(Webinar.webinar_date.asc()).all()

    # Track student registrations
    my_events = [r.event_id for r in EventRegistration.query.filter_by(student_id=student_id).all()]
    my_webinars = [r.webinar_id for r in WebinarRegistration.query.filter_by(student_id=student_id).all()]

    return render_template(
        'student/events.html',
        events=events_list,
        webinars=webinars_list,
        my_events=my_events,
        my_webinars=my_webinars
    )

# Register for Event
@student_bp.route('/register/event/<int:event_id>', methods=['POST'])
@student_required
def register_event(event_id):
    student_id = session['user_id']
    existing = EventRegistration.query.filter_by(student_id=student_id, event_id=event_id).first()

    if existing:
        flash("You are already registered for this event.", "info")
        return redirect(url_for('student.events'))

    reg = EventRegistration(student_id=student_id, event_id=event_id)
    db.session.add(reg)
    db.session.commit()
    flash("Registered for event successfully!", "success")
    return redirect(url_for('student.events'))

# Register for Webinar
@student_bp.route('/register/webinar/<int:webinar_id>', methods=['POST'])
@student_required
def register_webinar(webinar_id):
    student_id = session['user_id']
    existing = WebinarRegistration.query.filter_by(student_id=student_id, webinar_id=webinar_id).first()

    if existing:
        flash("You are already registered for this webinar.", "info")
        return redirect(url_for('student.events'))

    reg = WebinarRegistration(student_id=student_id, webinar_id=webinar_id)
    db.session.add(reg)
    db.session.commit()
    flash("Registered for webinar successfully! You can access the webinar link now.", "success")
    return redirect(url_for('student.events'))

# Jobs Search and browse
@student_bp.route('/jobs')
@student_required
def jobs():
    search_query = request.args.get('query', '').strip()
    if search_query:
        jobs_list = JobPosting.query.filter(
            JobPosting.title.like(f"%{search_query}%") |
            JobPosting.company.like(f"%{search_query}%") |
            JobPosting.requirements.like(f"%{search_query}%")
        ).order_by(JobPosting.created_at.desc()).all()
    else:
        jobs_list = JobPosting.query.order_by(JobPosting.created_at.desc()).all()
        
    return render_template('student/jobs.html', jobs=jobs_list, search_query=search_query)

# Mock Apply for Job
@student_bp.route('/jobs/apply/<int:job_id>', methods=['POST'])
@student_required
def apply_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    flash(f"Application submitted successfully for '{job.title}' at {job.company}! Your profile details have been shared with the alumnus.", "success")
    return redirect(url_for('student.jobs'))

# Student Chat
@student_bp.route('/messages')
@student_required
def messages():
    # Fetch connected alumni
    connections = MentorshipRequest.query.filter_by(student_id=session['user_id'], status='accepted').all()
    active_chat_alumni_id = request.args.get('chat_with')

    active_alumni = None
    if active_chat_alumni_id:
        active_alumni = Alumni.query.get(active_chat_alumni_id)

    return render_template('student/messages.html', connections=connections, active_alumni=active_alumni)

# ─────────────────────────────────────────────────────────────────────
# AI Alumni Recommendations – Dedicated Page
# ─────────────────────────────────────────────────────────────────────
@student_bp.route('/ai-recommendations')
@student_required
def ai_recommendations():
    student = Student.query.get(session['user_id'])

    # Read optional client-side filters from query params
    filter_skill    = request.args.get('skill', '').strip().lower()
    filter_company  = request.args.get('company', '').strip().lower()
    filter_location = request.args.get('location', '').strip().lower()
    filter_role     = request.args.get('role', '').strip().lower()

    # Get all recommendations (higher limit, include already-connected so page is always populated)
    rec_alumni, _ = get_ai_recommendations(student, limit=50, include_connected=True)

    # Apply additional filters
    if filter_skill:
        rec_alumni = [
            r for r in rec_alumni
            if filter_skill in (r['alumni'].skills or '').lower()
        ]
    if filter_company:
        rec_alumni = [
            r for r in rec_alumni
            if filter_company in (r['alumni'].company or '').lower()
        ]
    if filter_location:
        rec_alumni = [
            r for r in rec_alumni
            if filter_location in (r['alumni'].company or '').lower()
               or filter_location in (r['alumni'].domain or '').lower()
               or filter_location in (r['alumni'].designation or '').lower()
        ]
    if filter_role:
        rec_alumni = [
            r for r in rec_alumni
            if filter_role in (r['alumni'].designation or '').lower()
               or filter_role in (r['alumni'].domain or '').lower()
        ]

    # Connection status map for button states
    student_id = session['user_id']
    connections = {
        c.alumni_id: c.status
        for c in MentorshipRequest.query.filter_by(student_id=student_id).all()
    }

    # Profile completeness hint (0–100)
    filled = sum([
        bool(student.skills),
        bool(student.domain),
        bool(student.job_location),
    ])
    profile_score = int((filled / 3) * 100)

    return render_template(
        'student/ai_recommendations.html',
        student=student,
        rec_alumni=rec_alumni,
        connections=connections,
        profile_score=profile_score,
        filter_skill=filter_skill,
        filter_company=filter_company,
        filter_location=filter_location,
        filter_role=filter_role,
    )
