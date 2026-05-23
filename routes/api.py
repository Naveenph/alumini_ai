from flask import Blueprint, jsonify, request, session
from models.base import db
from models.models import Message, Notification, Student, Alumni, JobPosting, Event, Webinar
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Send Chat Message
@api_bp.route('/chat/send', methods=['POST'])
def send_message():
    if 'user_id' not in session or 'role' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    sender_id = session['user_id']
    sender_role = session['role']
    
    data = request.get_json() or {}
    receiver_id = data.get('receiver_id')
    message_text = data.get('message', '').strip()
    
    if not receiver_id or not message_text:
        return jsonify({"success": False, "error": "Missing fields"}), 400
        
    # Save message
    new_message = Message(
        sender_role=sender_role,
        sender_id=sender_id,
        receiver_id=int(receiver_id),
        message=message_text
    )
    db.session.add(new_message)
    
    # Notify receiver about new message
    receiver_role = 'alumni' if sender_role == 'student' else 'student'
    notif = Notification(
        user_role=receiver_role,
        user_id=int(receiver_id),
        message=f"New message from {session['name']}: '{message_text[:30]}...'"
    )
    db.session.add(notif)
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": {
            "id": new_message.id,
            "sender_role": new_message.sender_role,
            "sender_id": new_message.sender_id,
            "receiver_id": new_message.receiver_id,
            "message": new_message.message,
            "created_at": new_message.created_at.strftime("%I:%M %p")
        }
    })

# Fetch Chat History
@api_bp.route('/chat/history/<int:other_id>')
def get_chat_history(other_id):
    if 'user_id' not in session or 'role' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    user_id = session['user_id']
    role = session['role']
    
    # If I am a student, the other_id is an alumni, and vice-versa
    # Fetch messages where (sender is student and receiver is alumni) OR (sender is alumni and receiver is student)
    if role == 'student':
        messages = Message.query.filter(
            ((Message.sender_role == 'student') & (Message.sender_id == user_id) & (Message.receiver_id == other_id)) |
            ((Message.sender_role == 'alumni') & (Message.sender_id == other_id) & (Message.receiver_id == user_id))
        ).order_by(Message.created_at.asc()).all()
    else: # I am alumni
        messages = Message.query.filter(
            ((Message.sender_role == 'alumni') & (Message.sender_id == user_id) & (Message.receiver_id == other_id)) |
            ((Message.sender_role == 'student') & (Message.sender_id == other_id) & (Message.receiver_id == user_id))
        ).order_by(Message.created_at.asc()).all()

    # Mark as read
    for msg in messages:
        if msg.sender_role != role:
            msg.is_read = True
    db.session.commit()
    
    history = []
    for msg in messages:
        history.append({
            "id": msg.id,
            "sender_role": msg.sender_role,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "message": msg.message,
            "created_at": msg.created_at.strftime("%I:%M %p")
        })
        
    return jsonify({"success": True, "history": history})

# Fetch Unread Notifications count and messages
@api_bp.route('/notifications')
def get_notifications():
    if 'user_id' not in session or 'role' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    user_id = session['user_id']
    role = session['role']
    
    notifications = Notification.query.filter_by(
        user_role=role, 
        user_id=user_id, 
        is_read=False
    ).order_by(Notification.created_at.desc()).all()
    
    notif_list = [{"id": n.id, "message": n.message, "created_at": n.created_at.strftime("%d %b, %H:%M")} for n in notifications]
    
    return jsonify({
        "success": True,
        "count": len(notif_list),
        "notifications": notif_list
    })

# Admin Charts Analytics Data
@api_bp.route('/admin/analytics')
def admin_analytics():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    # Get stats
    alumni_count = Alumni.query.count()
    student_count = Student.query.count()
    job_count = JobPosting.query.count()
    event_count = Event.query.count()
    webinar_count = Webinar.query.count()
    
    # Approved vs Pending
    alumni_approved = Alumni.query.filter_by(is_approved=True).count()
    alumni_pending = Alumni.query.filter_by(is_approved=False).count()
    student_approved = Student.query.filter_by(is_approved=True).count()
    student_pending = Student.query.filter_by(is_approved=False).count()
    
    return jsonify({
        "success": True,
        "distribution": {
            "alumni": alumni_count,
            "students": student_count
        },
        "activities": {
            "jobs": job_count,
            "events": event_count,
            "webinars": webinar_count
        },
        "approvals": {
            "alumni_approved": alumni_approved,
            "alumni_pending": alumni_pending,
            "student_approved": student_approved,
            "student_pending": student_pending
        }
    })
