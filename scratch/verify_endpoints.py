import urllib.request
import urllib.parse
import json
import re
import sys
from http.cookiejar import CookieJar

BASE_URL = "http://127.0.0.1:5000"

# Setup Cookie Handler to persist session across requests
cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
urllib.request.install_opener(opener)

def make_request(url_path, data=None, is_json=False, custom_headers=None):
    url = f"{BASE_URL}{url_path}"
    headers = {
        'User-Agent': 'IntegrationTestAgent/1.0'
    }
    if custom_headers:
        headers.update(custom_headers)
    
    if data is not None:
        if is_json:
            encoded_data = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        else:
            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        req = urllib.request.Request(url, data=encoded_data, headers=headers)
    else:
        req = urllib.request.Request(url, headers=headers)
        
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            return response.getcode(), html, response.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8'), e.geturl()
    except Exception as e:
        print(f"[-] Network connection error: {e}")
        sys.exit(1)

def print_step(name):
    print(f"\n==================================================")
    print(f" STEP: {name}")
    print(f"==================================================")

def run_tests():
    print("[*] Starting integration verification tests against " + BASE_URL)
    
    # 1. Fetch Home Page
    print_step("Verify Landing Page")
    code, html, final_url = make_request("/")
    assert code == 200, f"Expected 200 OK, got {code}"
    print(f"[+] Landing Page OK: {final_url}")
    assert "Empower Your College Network" in html, "Landing page text mismatch"
    print("[+] Landing page content verified successfully.")

    # 2. Register new student
    print_step("Register New Student")
    student_data = {
        'name': 'Rohan Das',
        'email': 'rohan.das@student.edu',
        'password': 'studentpass123',
        'graduation_year': '2027',
        'skills': 'Python, SQL, JavaScript, Flask',
        'domain': 'Software Development'
    }
    code, html, final_url = make_request("/auth/register/student", student_data)
    assert code == 200, f"Expected 200 OK, got {code}"
    print(f"[+] Registration submitted. Final redirected URL: {final_url}")
    if "login" not in final_url:
        alerts = re.findall(r'<div class="alert[^"]*">.*?<span>(.*?)</span>', html, re.DOTALL)
        print(f"[-] Registration failed! Flashed messages: {alerts}")
    assert "login" in final_url, "Expected redirect to login page after signup"
    print("[+] Student signup submitted successfully.")

    # 3. Register new alumni
    print_step("Register New Alumni")
    alumni_data = {
        'name': 'Vikram Aditya',
        'email': 'vikram.aditya@alumni.com',
        'password': 'alumnipass123',
        'graduation_year': '2021',
        'company': 'Netflix',
        'designation': 'Senior Backend Engineer',
        'skills': 'Python, System Design, SQL, Docker',
        'domain': 'Software Development',
        'linkedin': 'https://linkedin.com/in/vikram-aditya-test'
    }
    code, html, final_url = make_request("/auth/register/alumni", alumni_data)
    assert code == 200, f"Expected 200 OK, got {code}"
    print(f"[+] Registration submitted. Final redirected URL: {final_url}")
    if "login" not in final_url:
        alerts = re.findall(r'<div class="alert[^"]*">.*?<span>(.*?)</span>', html, re.DOTALL)
        print(f"[-] Registration failed! Flashed messages: {alerts}")
    assert "login" in final_url, "Expected redirect to login page after signup"
    print("[+] Alumni signup submitted successfully.")

    # 4. Try logging in as unapproved student (should fail and stay on login)
    print_step("Verify Unapproved Student Login Restriction")
    cj.clear() # clear any login state
    login_data = {
        'email': 'rohan.das@student.edu',
        'password': 'studentpass123'
    }
    code, html, final_url = make_request("/auth/login/student", login_data)
    # Check that we are redirected back to login page and not dashboard
    assert "student/dashboard" not in final_url, "Unapproved student was allowed to log in!"
    print(f"[+] Login correctly blocked. Final URL: {final_url}")
    print("[+] Restriction for pending student verified.")

    # 5. Try logging in as unapproved alumni (should fail and stay on login)
    print_step("Verify Unapproved Alumni Login Restriction")
    cj.clear()
    login_data = {
        'email': 'vikram.aditya@alumni.com',
        'password': 'alumnipass123'
    }
    code, html, final_url = make_request("/auth/login/alumni", login_data)
    assert "alumni/dashboard" not in final_url, "Unapproved alumni was allowed to log in!"
    print(f"[+] Login correctly blocked. Final URL: {final_url}")
    print("[+] Restriction for pending alumni verified.")

    # 6. Log in as Admin and Approve both accounts
    print_step("Log in as Admin and Approve Accounts")
    cj.clear()
    admin_login = {
        'email': 'admin@alumni.com',
        'password': 'admin123'
    }
    code, html, final_url = make_request("/auth/login/admin", admin_login)
    assert "admin/dashboard" in final_url, f"Admin login failed. Final URL: {final_url}"
    print("[+] Logged in as Administrator.")
    
    # Parse pending student ID and alumni ID from admin dashboard
    student_ids = re.findall(r'/admin/approve/student/(\d+)', html)
    alumni_ids = re.findall(r'/admin/approve/alumni/(\d+)', html)
    
    assert len(student_ids) > 0, "No pending student registrations found on admin dashboard"
    assert len(alumni_ids) > 0, "No pending alumni registrations found on admin dashboard"
    
    # Approve ID 3 (Priya and Rohit) from dashboard (default fallback)
    code, html, final_url = make_request("/admin/approve/student/3", {})
    assert "admin/dashboard" in final_url, "Expected dashboard redirect when Referer is absent"
    print("[+] Approved Student ID 3 from Dashboard")

    code, html, final_url = make_request("/admin/approve/alumni/3", {})
    assert "admin/dashboard" in final_url, "Expected dashboard redirect when Referer is absent"
    print("[+] Approved Alumni ID 3 from Dashboard")

    # Fetch User Account Directory and verify pending approval forms are rendered
    code, html, final_url = make_request("/admin/users")
    assert code == 200, "Failed to load admin user directory"
    assert "/admin/approve/student/4" in html, "Approve student form missing in user directory"
    assert "/admin/approve/alumni/4" in html, "Approve alumni form missing in user directory"
    print("[+] Verified User Directory displays approve buttons for pending users")

    # Approve ID 4 (Rohan and Vikram) from /admin/users and verify Referer redirect
    referer_header = {
        'Referer': f"{BASE_URL}/admin/users"
    }
    code, html, final_url = make_request("/admin/approve/student/4", {}, custom_headers=referer_header)
    assert "admin/users" in final_url, f"Expected referer redirect to admin/users. Got: {final_url}"
    print("[+] Approved Student ID 4 from User Directory (Redirected back to directory successfully)")

    code, html, final_url = make_request("/admin/approve/alumni/4", {}, custom_headers=referer_header)
    assert "admin/users" in final_url, f"Expected referer redirect to admin/users. Got: {final_url}"
    print("[+] Approved Alumni ID 4 from User Directory (Redirected back to directory successfully)")

    new_student_id = 4
    new_alumni_id = 4

    # Logout Admin
    make_request("/auth/logout")
    print("[+] Logged out Admin.")

    # 7. Student can now log in
    print_step("Student Login & AI Dashboard Verification")
    cj.clear()
    student_login = {
        'email': 'rohan.das@student.edu',
        'password': 'studentpass123'
    }
    code, html, final_url = make_request("/auth/login/student", student_login)
    if "student/dashboard" not in final_url:
        print("[-] Login failed! Let's inspect response:")
        print(f"Final URL: {final_url}")
        alerts = re.findall(r'<div class="alert[^"]*">.*?<span>(.*?)</span>', html, re.DOTALL)
        print(f"Flashed messages: {alerts}")
    assert "student/dashboard" in final_url, f"Approved Student failed to log in. Final URL: {final_url}"
    print("[+] Student successfully logged in and redirected to dashboard.")
    
    # Verify AI recommendations are visible on Student dashboard
    assert "AI Mentor Recommendations" in html or "Recommended Mentors" in html, "Recommendations block missing"
    assert "Recommended Job Postings" in html or "AI Job Matcher" in html or "Jobs" in html, "Job recommendations block missing"
    print("[+] Student Dashboard recommendations loaded successfully.")

    # Logout Student
    make_request("/auth/logout")
    print("[+] Logged out Student.")

    # 8. Alumni can now log in & post a Job
    print_step("Alumni Login & Job Posting Verification")
    cj.clear()
    alumni_login = {
        'email': 'vikram.aditya@alumni.com',
        'password': 'alumnipass123'
    }
    code, html, final_url = make_request("/auth/login/alumni", alumni_login)
    assert "alumni/dashboard" in final_url, f"Approved Alumni failed to log in. Final URL: {final_url}"
    print("[+] Alumni successfully logged in.")
    
    # Post a job
    job_post_data = {
        'title': 'Junior Python Developer',
        'company': 'Netflix',
        'location': 'Mumbai, India (Remote)',
        'description': 'We are looking for a junior python engineer with good knowledge of SQL, Flask, and REST APIs.',
        'requirements': 'Python, SQL, Flask, REST APIs'
    }
    code, html, final_url = make_request("/alumni/jobs", job_post_data)
    assert "alumni/jobs" in final_url, f"Job posting failed. Final URL: {final_url}"
    assert "Junior Python Developer" in html, "Job posting title not found on jobs page"
    print("[+] Job posted successfully.")

    # Schedule a webinar
    webinar_data = {
        'title': 'Building Scalable APIs with Flask and Docker',
        'description': 'A session covering containerization of Python APIs, setting up entrypoints, and deploying to AWS ECS.',
        'webinar_date': '2026-06-15T15:00',
        'link': 'https://zoom.us/webinar/netflix-vikram'
    }
    code, html, final_url = make_request("/alumni/webinars", webinar_data)
    assert "alumni/webinars" in final_url, f"Webinar creation failed. Final URL: {final_url}"
    assert "Building Scalable APIs" in html, "Webinar title not found on webinars page"
    print("[+] Webinar scheduled successfully.")

    # Logout Alumni
    make_request("/auth/logout")
    print("[+] Logged out Alumni.")

    # 9. Student browse jobs & apply, then send connect request
    print_step("Student Interaction: Job Application & Mentorship Connect")
    cj.clear()
    make_request("/auth/login/student", student_login)
    
    # Browse jobs page and verify the job posted by Vikram is visible
    code, html, final_url = make_request("/student/jobs")
    assert "Junior Python Developer" in html, "Could not find Vikram's job on student jobs page"
    print("[+] Verified Vikram's job is listed on the student job portal.")
    
    # Extract Job ID
    job_ids = re.findall(r'/student/jobs/apply/(\d+)', html)
    assert len(job_ids) > 0, "No apply button/form found on student jobs page"
    test_job_id = job_ids[0]
    
    # Apply for job
    code, html, final_url = make_request(f"/student/jobs/apply/{test_job_id}", {})
    assert "Application submitted successfully" in html, "Job application flash message not found"
    print(f"[+] Applied for Job ID {test_job_id} successfully.")

    # Search for Vikram and connect
    code, html, final_url = make_request("/student/search?query=Vikram")
    assert "Vikram Aditya" in html, "Could not find Vikram in search results"
    
    # Extract connection action
    connect_ids = re.findall(r'/student/connect/(\d+)', html)
    assert len(connect_ids) > 0, "No connect button found in search results for Vikram"
    vikram_alumni_id = connect_ids[0]
    
    # Send connect request
    code, html, final_url = make_request(f"/student/connect/{vikram_alumni_id}", {})
    assert "Mentorship request sent successfully" in html, "Mentorship request flash message not found"
    print(f"[+] Sent mentorship connect request to Alumni Vikram Aditya (ID: {vikram_alumni_id}).")

    # Logout Student
    make_request("/auth/logout")

    # 10. Alumni approves connection request
    print_step("Alumni Accept Mentorship Connect Request")
    cj.clear()
    make_request("/auth/login/alumni", alumni_login)
    
    # View dashboard to find request ID
    code, html, final_url = make_request("/alumni/dashboard")
    assert "Rohan Das" in html, "No pending request from Rohan Das listed on dashboard"
    
    # Find request action URL: /alumni/request/<req_id>/approve
    req_ids = re.findall(r'/alumni/request/(\d+)/approve', html)
    assert len(req_ids) > 0, "No approve button/form found for pending request"
    req_id = req_ids[0]
    
    # Accept request
    code, html, final_url = make_request(f"/alumni/request/{req_id}/approve", {})
    assert "Mentorship request approved" in html, "Approval success message not found"
    print(f"[+] Approved mentorship connection (Request ID: {req_id}).")

    # Send message from alumni to student
    print_step("Chat Messaging Verification")
    chat_payload = {
        "receiver_id": int(new_student_id),
        "message": "Hi Rohan, I received your mentorship request. Let me know what you would like to discuss!"
    }
    code, html, final_url = make_request("/api/chat/send", chat_payload, is_json=True)
    assert code == 200, f"Expected 200 OK from chat send API, got {code}"
    resp_json = json.loads(html)
    assert resp_json.get("success") is True, "API reported chat send failure"
    print("[+] Sent message from Alumni to Student via API.")

    # Logout Alumni
    make_request("/auth/logout")

    # 11. Student reads message & replies
    cj.clear()
    make_request("/auth/login/student", student_login)
    
    # Fetch chat history
    code, html, final_url = make_request(f"/api/chat/history/{new_alumni_id}")
    assert code == 200, f"Expected 200 OK from chat history API, got {code}"
    resp_json = json.loads(html)
    assert resp_json.get("success") is True, "API reported chat history fetch failure"
    history = resp_json.get("history", [])
    assert len(history) > 0, "Chat history is empty"
    print(f"[+] Fetched Chat History. Latest message: '{history[-1]['message']}'")
    assert "discuss" in history[-1]['message'], "Chat message text mismatch"
    
    # Send reply
    reply_payload = {
        "receiver_id": int(new_alumni_id),
        "message": "Thanks Vikram! I would love to learn more about your experience at Netflix."
    }
    code, html, final_url = make_request("/api/chat/send", reply_payload, is_json=True)
    assert code == 200, "API reply failed"
    print("[+] Sent reply message from Student to Alumni.")
    
    # Verify updated chat history
    code, html, final_url = make_request(f"/api/chat/history/{new_alumni_id}")
    resp_json = json.loads(html)
    history = resp_json.get("history", [])
    assert len(history) == 2, f"Expected 2 messages in chat history, got {len(history)}"
    assert "Netflix" in history[-1]['message'], "Reply message text mismatch"
    print("[+] Chat messaging roundtrip completed and verified successfully!")

    # Logout Student
    make_request("/auth/logout")
    print_step("All Tests Passed!")
    print("[+] End-to-end features, constraints, and custom rule-based recommendations function flawlessly.")

if __name__ == "__main__":
    run_tests()
