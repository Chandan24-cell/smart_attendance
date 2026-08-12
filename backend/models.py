from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class AdminUser(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='Admin')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    registration_no = db.Column(db.String(30), unique=True, nullable=False)
    department = db.Column(db.String(100))
    year = db.Column(db.String(20))
    section = db.Column(db.String(10))
    email = db.Column(db.String(100))
    photo_status = db.Column(db.String(20))
    enrollment_status = db.Column(db.String(20), default='Not Enrolled')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class Subject(db.Model):
    __tablename__ = 'subjects'
    subject_id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)


class PeriodSchedule(db.Model):
    __tablename__ = 'period_schedule'
    schedule_id = db.Column(db.Integer, primary_key=True)
    period_number = db.Column(db.Integer, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.subject_id'))
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    is_break = db.Column(db.Boolean, default=False)
    grace_minutes = db.Column(db.Integer, default=15)
    is_active = db.Column(db.Boolean, default=True)


class AttendanceSession(db.Model):
    __tablename__ = 'attendance_sessions'
    session_id = db.Column(db.Integer, primary_key=True)
    session_date = db.Column(db.String(20))
    schedule_id = db.Column(db.Integer, db.ForeignKey('period_schedule.schedule_id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.subject_id'))
    period_number = db.Column(db.Integer)
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    cutoff_time = db.Column(db.String(10))
    session_status = db.Column(db.String(20), default='Scheduled')
    created_at = db.Column(db.DateTime, default=datetime.now)


class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    attendance_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_sessions.session_id'))
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    status = db.Column(db.String(30), default='Absent')
    detected_time = db.Column(db.String(10))
    method = db.Column(db.String(20), default='Automatic')
    updated_by = db.Column(db.String(50))
    update_reason = db.Column(db.String(200))
    marked_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)


class AuditLog(db.Model):
    __tablename__ = 'attendance_audit_logs'
    log_id = db.Column(db.Integer, primary_key=True)
    attendance_id = db.Column(db.Integer, db.ForeignKey('attendance_records.attendance_id'))
    old_status = db.Column(db.String(30))
    new_status = db.Column(db.String(30))
    reason = db.Column(db.String(200))
    changed_by = db.Column(db.String(50))
    changed_at = db.Column(db.DateTime, default=datetime.now)


class SyncLog(db.Model):
    __tablename__ = 'sync_logs'
    sync_id = db.Column(db.Integer, primary_key=True)
    source_type = db.Column(db.String(30))
    sync_type = db.Column(db.String(30))
    sync_status = db.Column(db.String(20))
    total_rows_read = db.Column(db.Integer, default=0)
    new_records_added = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)
    records_skipped = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    last_sync_at = db.Column(db.DateTime, default=datetime.now)


class Setting(db.Model):
    __tablename__ = 'settings'
    setting_id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True)
    setting_value = db.Column(db.String(100))


class FaceEmbedding(db.Model):
    __tablename__ = 'face_embeddings'
    embedding_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'))
    embedding = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    enrolled_at = db.Column(db.DateTime, default=datetime.now)


class DetectionLog(db.Model):
    __tablename__ = 'detection_logs'
    log_id = db.Column(db.Integer, primary_key=True)
    detected_at = db.Column(db.DateTime, default=datetime.now)
    student_id = db.Column(db.Integer, nullable=True)
    roll_no = db.Column(db.String(20))
    name = db.Column(db.String(100))
    event_type = db.Column(db.String(30))
    session_id = db.Column(db.Integer, nullable=True)
    camera_source = db.Column(db.String(100))
