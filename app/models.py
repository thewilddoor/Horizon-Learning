# app/models.py

from flask_login import UserMixin
from . import db
import uuid
import random
import string
from datetime import datetime

# Association tables
learning_companion_material = db.Table('learning_companion_material',
    db.Column('learning_companion_id', db.Integer, db.ForeignKey('learning_companion.id'), primary_key=True),
    db.Column('material_id', db.Integer, db.ForeignKey('material.id'), primary_key=True)
)

student_learning_companion = db.Table('student_learning_companion',
    db.Column('student_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('learning_companion_id', db.Integer, db.ForeignKey('learning_companion.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin', 'teacher', 'student'
    
    # For teachers
    school_name = db.Column(db.String(128), nullable=True)
    learning_companions = db.relationship('LearningCompanion', backref='teacher', lazy=True)
    
    # For students
    class_code = db.Column(db.String(10), nullable=True)
    learning_companions = db.relationship('LearningCompanion', secondary=student_learning_companion, backref='students')
    
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_student(self):
        return self.role == 'student'
    
    def __repr__(self):
        return f'<User {self.name} - {self.role}>'

class Bot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    bot_id = db.Column(db.String(64), unique=True, nullable=False)
    api_token = db.Column(db.String(256), nullable=False)
    
    learning_companions = db.relationship('LearningCompanion', backref='bot', lazy=True)
    
    def __repr__(self):
        return f'<Bot {self.name}>'

class LearningCompanion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(64), nullable=False)
    subject = db.Column(db.String(64), nullable=False)
    instructions = db.Column(db.Text, nullable=True)
    class_code = db.Column(db.String(10), unique=True, nullable=False, default=lambda: generate_class_code())
    
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'), nullable=False)
    
    materials = db.relationship('Material', secondary=learning_companion_material, backref='learning_companions')
    
    def __repr__(self):
        return f'<LearningCompanion {self.class_name} - {self.subject}>'

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    def __repr__(self):
        return f'<Material {self.filename}>'

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    summary = db.Column(db.Text, nullable=False)
    
    teacher = db.relationship('User', backref='reports')
    
    def __repr__(self):
        return f'<Report {self.date} - Teacher ID {self.teacher_id}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable to allow AI messages
    companion_id = db.Column(db.Integer, db.ForeignKey('learning_companion.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    conversation_id = db.Column(db.String(36), nullable=True)  # UUID for conversation
    
    sender_type = db.Column(db.String(10), nullable=False)  # 'student' or 'AI'
    
    def __repr__(self):
        return f'<Message {self.id} from User {self.user_id} in Companion {self.companion_id}>'


def generate_class_code(length=6):
    """Generates a unique alphanumeric class code."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not LearningCompanion.query.filter_by(class_code=code).first():
            break
    return code
