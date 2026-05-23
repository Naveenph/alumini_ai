-- MySQL Schema for Alumni Network System
-- Matches SQLite & MySQL standards

-- Create database if not exists (for MySQL setup)
CREATE DATABASE IF NOT EXISTS alumni_db;
USE alumni_db;

-- 1. Admin Table
CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    profile_pic VARCHAR(255) DEFAULT 'default_admin.png',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Alumni Table (needs approval from admin)
CREATE TABLE IF NOT EXISTS alumni (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    company VARCHAR(100) DEFAULT NULL,
    designation VARCHAR(100) DEFAULT NULL,
    skills VARCHAR(255) DEFAULT NULL, -- comma separated skills
    domain VARCHAR(100) DEFAULT NULL, -- domain of work (e.g., Software, Finance, HR)
    graduation_year INT NOT NULL,
    linkedin VARCHAR(255) DEFAULT NULL,
    profile_pic VARCHAR(255) DEFAULT 'default_avatar.png',
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Students Table (needs approval from admin)
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    skills VARCHAR(255) DEFAULT NULL, -- comma separated skills
    domain VARCHAR(100) DEFAULT NULL, -- domain of interest (e.g., Software, Finance)
    graduation_year INT NOT NULL,
    profile_pic VARCHAR(255) DEFAULT 'default_avatar.png',
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Events Table (created by Admins for Students)
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    event_date DATETIME NOT NULL,
    location VARCHAR(150) NOT NULL, -- e.g. 'Virtual', 'Seminar Hall A'
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES admin(id) ON DELETE CASCADE
);

-- 5. Webinars Table (created by Alumni for Students)
CREATE TABLE IF NOT EXISTS webinar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    webinar_date DATETIME NOT NULL,
    link VARCHAR(255) NOT NULL, -- Link to Join (Zoom, Meet, etc.)
    speaker_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (speaker_id) REFERENCES alumni(id) ON DELETE CASCADE
);

-- 6. Event Registrations (Students registering for Admin events)
CREATE TABLE IF NOT EXISTS event_registration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    event_id INT NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_event (student_id, event_id)
);

-- 7. Webinar Registrations (Students registering for Alumni webinars)
CREATE TABLE IF NOT EXISTS webinar_registration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    webinar_id INT NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (webinar_id) REFERENCES webinar(id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_webinar (student_id, webinar_id)
);

-- 8. Job Postings (Created by Alumni)
CREATE TABLE IF NOT EXISTS job_postings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    company VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT NOT NULL, -- comma separated skills/requirements
    posted_by_alumni_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (posted_by_alumni_id) REFERENCES alumni(id) ON DELETE CASCADE
);

-- 9. Mentorship / Connections Requests (Between Students and Alumni)
CREATE TABLE IF NOT EXISTS mentorship_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    alumni_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'accepted', 'rejected'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (alumni_id) REFERENCES alumni(id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_alumni (student_id, alumni_id)
);

-- 10. Messages (Chat between students and alumni)
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_role VARCHAR(10) NOT NULL, -- 'student' or 'alumni'
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL, -- if sender is student, receiver is alumni, and vice-versa
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_role VARCHAR(10) NOT NULL, -- 'admin', 'alumni', 'student'
    user_id INT NOT NULL,
    message VARCHAR(255) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. Activity Logs (For Admin view)
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(255) NOT NULL,
    details TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. AI Recommendation (Matches students with recommended alumni mentors or job postings)
CREATE TABLE IF NOT EXISTS ai_recommendation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    recommendation_type VARCHAR(20) NOT NULL, -- 'alumni' or 'job'
    recommended_item_id INT NOT NULL, -- id from alumni or job_postings
    score INT NOT NULL, -- match percentage or score
    reason VARCHAR(255) NOT NULL, -- reasoning text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);
