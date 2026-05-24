from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models.base import db

# 1. Admin Model
class Admin(db.Model):
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_pic = db.Column(db.String(255), default='default_admin.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    events = db.relationship('Event', backref='admin_creator', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 2. Alumni Model
class Alumni(db.Model):
    __tablename__ = 'alumni'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(100), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    skills = db.Column(db.String(255), nullable=True) # Comma-separated list of skills
    domain = db.Column(db.String(100), nullable=True) # Domain of work
    graduation_year = db.Column(db.Integer, nullable=False)
    linkedin = db.Column(db.String(255), nullable=True)
    profile_pic = db.Column(db.String(255), default='default_avatar.png')
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    webinars = db.relationship('Webinar', backref='speaker', lazy=True, cascade="all, delete-orphan")
    jobs = db.relationship('JobPosting', backref='poster', lazy=True, cascade="all, delete-orphan")
    mentorship_requests = db.relationship('MentorshipRequest', backref='alumni', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 3. Student Model
class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    skills = db.Column(db.String(255), nullable=True) # Comma-separated list of skills
    domain = db.Column(db.String(100), nullable=True) # Domain of interest
    job_location = db.Column(db.String(100), nullable=True) # Preferred job location (e.g. "Bangalore", "Remote")
    graduation_year = db.Column(db.Integer, nullable=False)
    profile_pic = db.Column(db.String(255), default='default_avatar.png')
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    event_registrations = db.relationship('EventRegistration', backref='student', lazy=True, cascade="all, delete-orphan")
    webinar_registrations = db.relationship('WebinarRegistration', backref='student', lazy=True, cascade="all, delete-orphan")
    mentorship_requests = db.relationship('MentorshipRequest', backref='student', lazy=True, cascade="all, delete-orphan")
    ai_recommendations = db.relationship('AIRecommendation', backref='student', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 4. Event Model (conducted by Admin)
class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    registrations = db.relationship('EventRegistration', backref='event', lazy=True, cascade="all, delete-orphan")

# 5. Webinar Model (conducted by Alumni)
class Webinar(db.Model):
    __tablename__ = 'webinar'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    webinar_date = db.Column(db.DateTime, nullable=False)
    link = db.Column(db.String(255), nullable=False) # e.g. zoom link
    speaker_id = db.Column(db.Integer, db.ForeignKey('alumni.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    registrations = db.relationship('WebinarRegistration', backref='webinar', lazy=True, cascade="all, delete-orphan")

# 6. Event Registration (Student -> Event)
class EventRegistration(db.Model):
    __tablename__ = 'event_registration'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id', ondelete='CASCADE'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('student_id', 'event_id', name='unique_student_event'),)

# 7. Webinar Registration (Student -> Webinar)
class WebinarRegistration(db.Model):
    __tablename__ = 'webinar_registration'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    webinar_id = db.Column(db.Integer, db.ForeignKey('webinar.id', ondelete='CASCADE'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('student_id', 'webinar_id', name='unique_student_webinar'),)

# 8. Job Postings (posted by Alumni)
class JobPosting(db.Model):
    __tablename__ = 'job_postings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=False) # comma-separated list of skills
    posted_by_alumni_id = db.Column(db.Integer, db.ForeignKey('alumni.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 9. Mentorship Requests / Connections (Student -> Alumni)
class MentorshipRequest(db.Model):
    __tablename__ = 'mentorship_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    alumni_id = db.Column(db.Integer, db.ForeignKey('alumni.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='pending') # 'pending', 'accepted', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('student_id', 'alumni_id', name='unique_student_alumni'),)

# 10. Messages (Chat)
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_role = db.Column(db.String(10), nullable=False) # 'student' or 'alumni'
    sender_id = db.Column(db.Integer, nullable=False)
    receiver_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 11. Notifications
class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_role = db.Column(db.String(10), nullable=False) # 'admin', 'alumni', 'student'
    user_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 12. Activity Logs (Admin dashboard activity logs)
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 13. AI Recommendation Logs
class AIRecommendation(db.Model):
    __tablename__ = 'ai_recommendation'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    recommendation_type = db.Column(db.String(20), nullable=False) # 'alumni' or 'job'
    recommended_item_id = db.Column(db.Integer, nullable=False) # ID of the alumni or job posting
    score = db.Column(db.Integer, nullable=False) # Recommendation match percentage e.g., 85
    reason = db.Column(db.String(255), nullable=False) # Reasoning string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
