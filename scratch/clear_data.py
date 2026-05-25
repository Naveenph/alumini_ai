import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.models import Alumni, Student, MentorshipRequest, JobPosting, Event, Webinar, Message, Notification, EventRegistration, WebinarRegistration, ActivityLog, AIRecommendation, FlashcardImage

with app.app_context():
    try:
        # Delete dependent tables first to avoid foreign key constraint errors
        Message.query.delete()
        Notification.query.delete()
        ActivityLog.query.delete()
        AIRecommendation.query.delete()
        EventRegistration.query.delete()
        WebinarRegistration.query.delete()
        MentorshipRequest.query.delete()
        JobPosting.query.delete()
        Webinar.query.delete()
        Event.query.delete()
        FlashcardImage.query.delete()
        
        # Now delete core users
        Student.query.delete()
        Alumni.query.delete()
        
        db.session.commit()
        print("Successfully removed all fake users, events, jobs, and requests.")
    except Exception as e:
        db.session.rollback()
        print(f"Error during cleanup: {e}")
