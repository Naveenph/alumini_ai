import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.models import Admin, Alumni, Student

with app.app_context():
    print("--- Admins ---")
    for a in Admin.query.all():
        print(f"ID: {a.id}, Email: {a.email}")
    
    print("\n--- Alumni ---")
    for a in Alumni.query.all():
        print(f"ID: {a.id}, Email: {a.email}, Verified: {a.is_email_verified}, Approved: {a.is_approved}, OTP: {a.email_verification_otp}")
    
    print("\n--- Students ---")
    for s in Student.query.all():
        print(f"ID: {s.id}, Email: {s.email}, Verified: {s.is_email_verified}, Approved: {s.is_approved}, OTP: {s.email_verification_otp}")
