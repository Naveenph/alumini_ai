import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models.base import db
from models.models import Admin, Alumni, Student, Event, Webinar, JobPosting, MentorshipRequest, Message, Notification, ActivityLog
from app import app

load_dotenv()

def seed_database():
    print("[*] Starting database seeding process...")
    
    # 1. Re-create all tables
    db.drop_all()
    db.create_all()
    print("[+] Database tables re-created.")

    # 2. Seed Admin
    admin = Admin(name="College Administrator", email="admin@alumni.com")
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    print("[+] Seeded Admin: admin@alumni.com / admin123")

    # 3. Seed Students
    student1 = Student(
        name="Aman Gupta",
        email="aman@student.edu",
        skills="Python, SQL, JavaScript, HTML, CSS",
        domain="Software Development",
        graduation_year=2027,
        is_approved=True
    )
    student1.set_password("student123")
    
    student2 = Student(
        name="Karan Johar",
        email="karan@student.edu",
        skills="Python, Pandas, NumPy, SQL, Machine Learning",
        domain="Data Science",
        graduation_year=2026,
        is_approved=True
    )
    student2.set_password("student123")

    # Pending approval student
    student_pending = Student(
        name="Priya Das",
        email="priya@student.edu",
        skills="SEO, Content Writing, Excel",
        domain="Marketing",
        graduation_year=2027,
        is_approved=False
    )
    student_pending.set_password("student123")

    db.session.add_all([student1, student2, student_pending])
    db.session.commit()
    print("[+] Seeded Students (Aman: approved, Karan: approved, Priya: pending)")

    # 4. Seed Alumni
    alumni1 = Alumni(
        name="Nitin Sharma",
        email="nitin@microsoft.com",
        company="Microsoft",
        designation="Software Engineer 2",
        skills="Java, C++, SQL, System Design, AWS",
        domain="Software Development",
        graduation_year=2022,
        linkedin="https://linkedin.com/in/nitin-sharma-demo",
        is_approved=True
    )
    alumni1.set_password("alumni123")

    alumni2 = Alumni(
        name="Sneha Reddy",
        email="sneha@google.com",
        company="Google",
        designation="Data Scientist",
        skills="Python, TensorFlow, SQL, Pandas, PyTorch",
        domain="Data Science",
        graduation_year=2020,
        linkedin="https://linkedin.com/in/sneha-reddy-demo",
        is_approved=True
    )
    alumni2.set_password("alumni123")

    # Pending approval alumni
    alumni_pending = Alumni(
        name="Rohit Verma",
        email="rohit@amazon.com",
        company="Amazon",
        designation="Product Manager",
        skills="Product Roadmapping, Agile, Scrum",
        domain="Product Management",
        graduation_year=2023,
        linkedin="https://linkedin.com/in/rohit-verma-demo",
        is_approved=False
    )
    alumni_pending.set_password("alumni123")

    db.session.add_all([alumni1, alumni2, alumni_pending])
    db.session.commit()
    print("[+] Seeded Alumni (Nitin: approved, Sneha: approved, Rohit: pending)")

    # 5. Seed Events (by Admin)
    event1 = Event(
        title="Annual Alumni Homecoming Meet 2026",
        description="Join us for the annual campus meetups where current students can network with senior alumni. Dinner and high-tea provided.",
        event_date=datetime.now() + timedelta(days=15, hours=3),
        location="Campus Main Auditorium",
        created_by=admin.id
    )

    event2 = Event(
        title="Pre-Placement Preparation BootCamp",
        description="A comprehensive guidance bootcamp hosted by campus placements coordinators. Covers resume building, mock interviews and DSA preparation.",
        event_date=datetime.now() + timedelta(days=7, hours=2),
        location="Seminar Hall B & Virtual Zoom",
        created_by=admin.id
    )

    db.session.add_all([event1, event2])
    db.session.commit()
    print("[+] Seeded Admin Events.")

    # 6. Seed Webinars (by Alumni)
    webinar1 = Webinar(
        title="Transitioning from Academics to Big Tech Careers",
        description="This session covers key tips on clearing technical interviews at Tier-1 tech companies, building a resume portfolio, and working on impactful side-projects.",
        webinar_date=datetime.now() + timedelta(days=5, hours=1),
        link="https://zoom.us/webinar/example-nitin",
        speaker_id=alumni1.id
    )

    webinar2 = Webinar(
        title="Applying Machine Learning in Production Environments",
        description="A practical session demonstrating how to build, deploy, and monitor ML pipelines using Python, SQL, and AWS. Ideal for aspiring data scientists.",
        webinar_date=datetime.now() + timedelta(days=12, hours=4),
        link="https://zoom.us/webinar/example-sneha",
        speaker_id=alumni2.id
    )

    db.session.add_all([webinar1, webinar2])
    db.session.commit()
    print("[+] Seeded Alumni Webinars.")

    # 7. Seed Job Postings (by Alumni)
    job1 = JobPosting(
        title="Software Engineering Intern (Summer 2026)",
        company="Microsoft",
        location="Bangalore, India (Hybrid)",
        requirements="Java, Python, Data Structures, Algorithms",
        description="We are looking for passionate computer science students for our summer internship. You will build cloud-scale features on Azure. Strong problem-solving skills required.",
        posted_by_alumni_id=alumni1.id
    )

    job2 = JobPosting(
        title="Associate Data Analyst",
        company="Google",
        location="Hyderabad, India",
        requirements="Python, SQL, Pandas, Tableau",
        description="Analyze large-scale search logs to improve query recommendations. Looking for recent graduates with strong SQL skills and analytical mindsets.",
        posted_by_alumni_id=alumni2.id
    )

    db.session.add_all([job1, job2])
    db.session.commit()
    print("[+] Seeded Alumni Job Listings.")

    # 8. Seed Mentorship Connections
    # Aman Gupta connected with Nitin Sharma
    conn1 = MentorshipRequest(student_id=student1.id, alumni_id=alumni1.id, status="accepted")
    # Karan Johar connected with Sneha Reddy
    conn2 = MentorshipRequest(student_id=student2.id, alumni_id=alumni2.id, status="accepted")
    # Aman Gupta requested connection with Sneha Reddy (pending)
    conn3 = MentorshipRequest(student_id=student1.id, alumni_id=alumni2.id, status="pending")

    db.session.add_all([conn1, conn2, conn3])
    db.session.commit()
    print("[+] Seeded Mentorship Requests / Connections.")

    # 9. Seed Chat Messages between Aman and Nitin
    msg1 = Message(sender_role="student", sender_id=student1.id, receiver_id=alumni1.id, message="Hello Nitin! Thanks for accepting my mentorship request. I am looking for some guidance on Azure cloud certifications.")
    msg2 = Message(sender_role="alumni", sender_id=alumni1.id, receiver_id=student1.id, message="Hi Aman! Glad to connect. For Azure, I'd suggest starting with the AZ-900 fundamentals, and then doing the AZ-204 Developer associate. Let me know if you need resources!")
    msg3 = Message(sender_role="student", sender_id=student1.id, receiver_id=alumni1.id, message="That makes sense! I'll look into AZ-900. Do you recommend any specific online courses?")
    
    db.session.add_all([msg1, msg2, msg3])
    db.session.commit()
    print("[+] Seeded Chat Messages.")

    # 10. Seed Notifications
    notif1 = Notification(user_role="student", user_id=student1.id, message="Alumnus Nitin Sharma accepted your mentorship request!")
    notif2 = Notification(user_role="student", user_id=student1.id, message="New Event Scheduled: 'Annual Alumni Homecoming Meet 2026'")
    
    db.session.add_all([notif1, notif2])
    
    # Activity Logs
    log1 = ActivityLog(action="Database Seeded", details="Dummy seed data loaded to tables.")
    db.session.add(log1)
    
    db.session.commit()
    print("[+] Seeded Notifications & Activity Logs.")
    print("[+] Seeding process completed successfully!")

if __name__ == '__main__':
    with app.app_context():
        seed_database()
