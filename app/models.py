# app/models.py
from .extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Chanda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    pattern = db.Column(db.String(200), nullable=False)
    syllable_count = db.Column(db.Integer, nullable=False)
    description_short = db.Column(db.Text, nullable=True)
    pariyat_url = db.Column(db.String(500), nullable=True)
    
    examples = db.relationship('VerseExample', backref='chanda', lazy='dynamic')
    
    def __repr__(self):
        return f"Chanda('{self.name}')"

class PoeticWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), unique=True, nullable=False, index=True)
    prosody = db.Column(db.String(50), nullable=False, index=True)
    meaning = db.Column(db.String(500))

class VerseExample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    layout_type = db.Column(db.String(20), nullable=False, default='4_lines_1_col')
    source_type = db.Column(db.String(50), index=True)
    source_details = db.Column(db.String(200))
    notes = db.Column(db.Text)
    translation = db.Column(db.Text, nullable=True) # <-- แก้ไขให้ถูกต้อง
    
    chanda_id = db.Column(db.Integer, db.ForeignKey('chanda.id'), nullable=False)