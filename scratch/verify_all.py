import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.models import Alumni, Student

with app.app_context():
    alumni = Alumni.query.all()
    for a in alumni:
        a.is_email_verified = True
    
    students = Student.query.all()
    for s in students:
        s.is_email_verified = True
        
    db.session.commit()
    print("All existing users have been verified.")
