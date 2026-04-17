from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime # ★ ADD THIS IMPORT AT THE TOP OF THE FILE

# Initialize db here, but don't tie it to an app yet
db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student') # Roles: 'superadmin', 'admin', 'student', 'parent'

    # Self-referential relationship for Parent-Child link
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    # Corrected relationship definition
    children = db.relationship('User', backref=db.backref('parent', remote_side=[id]))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_superadmin(self):
        return self.role == 'superadmin'

    @property
    def is_admin(self):
        return self.role in ['admin', 'superadmin']

    # Debug helper
    def __repr__(self):
        return f'<User {self.username} role={self.role}>'

class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    province = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    sector = db.Column(db.String(100), nullable=False)
    education_program = db.Column(db.String(100), nullable=False)
    gender_policy = db.Column(db.String(50), nullable=False)
    ownership = db.Column(db.String(100), nullable=False)
    religious_affiliation = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    photos = db.Column(db.Text, nullable=True)
    fees_file = db.Column(db.String(200), nullable=True)
    extracurriculars = db.Column(db.Text, nullable=True)
    tags = db.Column(db.Text, nullable=True)
    reviews = db.relationship('Review', backref='school', lazy=True, cascade="all, delete-orphan")
    boarding_policy = db.Column(db.String(50), nullable=False, default='Day School')
    # ★ ADD THIS LINE ★
    min_aggregate = db.Column(db.Integer, nullable=True, default=0)

    # New fields for Enhanced Dashboard
    combinations = db.Column(db.Text, nullable=True) # e.g., "MEG, PCB, MPC"
    fees_breakdown = db.Column(db.Text, nullable=True) # JSON or Text description
    performance_history = db.Column(db.Text, nullable=True) # JSON or Text description
    fee_band = db.Column(db.String(50), nullable=True, default='Not Published')
    language_of_instruction = db.Column(db.String(50), nullable=True, default='Other / Not Published')
    
     # A helper to easily calculate the average rating
    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        approved_reviews = [r for r in self.reviews if r.status == 'approved']
        if not approved_reviews:
            return 0
        total_rating = sum(r.rating for r in approved_reviews)
        return round(total_rating / len(approved_reviews), 1)

    # ... (your to_dict function is here) ...
# ★★★ END: SCHOOL MODEL UPDATE ★★★

    def to_dict(self):
        # We need to import url_for here as it's used
        from flask import url_for
        return {
            'id': self.id, 'name': self.name, 'province': self.province, 'district': self.district,
            'education_program': self.education_program, 'gender_policy': self.gender_policy,
            'ownership': self.ownership,
            'boarding_policy': self.boarding_policy,
            'fee_band': self.fee_band or 'Not Published',
            'language_of_instruction': self.language_of_instruction or 'Other / Not Published',
            'image_url': self.photos.split(',')[0].strip() if self.photos else url_for('static', filename='images/default_school.png')
        }

# ★★★ START: NEW SCHOOL SUGGESTION MODEL ★★★
class SchoolSuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    province = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    sector = db.Column(db.String(100), nullable=False)
    education_program = db.Column(db.String(100), nullable=False)
    gender_policy = db.Column(db.String(50), nullable=False)
    ownership = db.Column(db.String(100), nullable=False)
    religious_affiliation = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    photos = db.Column(db.Text, nullable=True) # URLs provided by user
    boarding_policy = db.Column(db.String(50), nullable=True)
    extracurriculars = db.Column(db.Text, nullable=True)
    # --- Tracking Fields ---
    suggester_name = db.Column(db.String(100), nullable=True)
    suggester_email = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending') # pending, approved, rejected
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<SchoolSuggestion {self.name}>'
# ★★★ END: NEW SCHOOL SUGGESTION MODEL ★★★
# ★★★ START: NEW REVIEW MODEL ★★★
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False) # A rating from 1 to 5
    comment = db.Column(db.Text, nullable=False)
    reviewer_name = db.Column(db.String(100), nullable=False, default='Anonymous')
    status = db.Column(db.String(20), nullable=False, default='pending') # pending, approved
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Foreign Key to link to a School
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)

    def __repr__(self):
        return f'<Review {self.id} for School {self.school_id}>'
# ★★★ END: NEW REVIEW MODEL ★★★

# ★★★ START: SHORTLIST MODEL ★★★
class Shortlist(db.Model):
    """Schools the student likes"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)

    # The Interaction Logic
    student_notes = db.Column(db.String(200), nullable=True) # "I like their robotics club"
    parent_status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    parent_comment = db.Column(db.String(200), nullable=True) # "Too expensive, look for another"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('User', backref='shortlists', foreign_keys=[student_id])
    school = db.relationship('School', backref='shortlists')
# ★★★ END: SHORTLIST MODEL ★★★
