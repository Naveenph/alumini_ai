import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from dotenv import load_dotenv
from models.base import db, mail
from models.models import Admin, Alumni, Student, ActivityLog
from database.connection import get_database_uri

# Load Environment Variables
load_dotenv()

# Initialize Flask App
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key_alumni_system_2026")

# Database Configuration
db_uri = get_database_uri()
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)

# Mail Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# Initialize Mail
mail.init_app(app)

# Register Blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.alumni import alumni_bp
from routes.student import student_bp
from routes.api import api_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp)
app.register_blueprint(alumni_bp)
app.register_blueprint(student_bp)
app.register_blueprint(api_bp)

# Create Default Profile Pictures Helper (using Pillow)
def generate_default_avatars():
    upload_dir = os.path.join("static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    avatar_path = os.path.join(upload_dir, "default_avatar.png")
    admin_avatar_path = os.path.join(upload_dir, "default_admin.png")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 1. Create Default Student/Alumni Avatar
        if not os.path.exists(avatar_path):
            img = Image.new("RGBA", (200, 200), color=(124, 58, 237, 255)) # Violet HSL(245)
            draw = ImageDraw.Draw(img)
            # Draw a simple circle and torso profile representation
            draw.ellipse((60, 40, 140, 120), fill=(255, 255, 255, 255))
            draw.ellipse((30, 130, 170, 220), fill=(255, 255, 255, 255))
            img.save(avatar_path)
            print("[+] Generated default avatar image.")
            
        # 2. Create Default Admin Avatar
        if not os.path.exists(admin_avatar_path):
            img = Image.new("RGBA", (200, 200), color=(219, 39, 119, 255)) # Pink
            draw = ImageDraw.Draw(img)
            draw.ellipse((60, 40, 140, 120), fill=(255, 255, 255, 255))
            draw.ellipse((30, 130, 170, 220), fill=(255, 255, 255, 255))
            img.save(admin_avatar_path)
            print("[+] Generated default admin avatar image.")
            
    except ImportError:
        # Fallback if Pillow fails, write a text file rename or let it be
        print("[-] Pillow not installed, skipping dynamic placeholder avatar generation.")

# Database Initialization & Seeding
with app.app_context():
    # Create tables
    db.create_all()
    
    # Generate default asset files
    generate_default_avatars()
    
    # Seed default Admin account if empty
    default_admin_email = "admin@alumni.com"
    existing_admin = Admin.query.filter_by(email=default_admin_email).first()
    if not existing_admin:
        admin = Admin(name="College Administrator", email=default_admin_email)
        admin.set_password("admin123")
        db.session.add(admin)
        
        # Add a test log
        log = ActivityLog(action="Database Initialization", details="Default admin account seeded successfully.")
        db.session.add(log)
        
        db.session.commit()
        print(f"[+] Seeded default administrator: {default_admin_email} / admin123")

# 4. Public Core Page Handlers
@app.route('/')
def home():
    from models.models import Alumni, Student, Webinar, JobPosting, FlashcardImage
    
    # Real-time stats
    alumni_count = Alumni.query.filter_by(is_approved=True).count()
    student_count = Student.query.filter_by(is_approved=True).count()
    webinar_count = Webinar.query.count()
    job_count = JobPosting.query.count()
    
    # Flashcards
    flashcards = FlashcardImage.query.order_by(FlashcardImage.created_at.desc()).all()
    
    return render_template('index.html', 
                           alumni_count=alumni_count, 
                           student_count=student_count,
                           webinar_count=webinar_count,
                           job_count=job_count,
                           flashcards=flashcards)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # In a production system, this would write to a database contact table or email the admin
        # Here we flash success and redirect
        flash(f"Thank you, {name}! Your message regarding '{subject}' has been submitted to the college administration team.", "success")
        return redirect(url_for('home'))
        
    return render_template('contact.html')

# Run Server
if __name__ == '__main__':
    # Running locally in debug mode
    app.run(debug=True, port=5000)
