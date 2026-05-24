from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Модель пользователя"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' или 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'

class Pipeline(db.Model):
    """Модель трубопровода"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    length_km = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    defects = db.relationship('Defect', backref='pipeline', lazy=True)

class Defect(db.Model):
    """Модель дефекта трубопровода"""
    id = db.Column(db.Integer, primary_key=True)
    pipeline_id = db.Column(db.Integer, db.ForeignKey('pipeline.id'), nullable=False)
    km = db.Column(db.Float, nullable=False)
    defect_type = db.Column(db.String(50), nullable=False)
    depth_mm = db.Column(db.Float, nullable=False)
    length_mm = db.Column(db.Float, nullable=False)
    width_mm = db.Column(db.Float, nullable=True)
    risk_level = db.Column(db.String(20), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    recommendation = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'km': self.km,
            'defect_type': self.defect_type,
            'depth_mm': self.depth_mm,
            'length_mm': self.length_mm,
            'risk_level': self.risk_level,
            'risk_score': self.risk_score,
            'recommendation': self.recommendation
        }