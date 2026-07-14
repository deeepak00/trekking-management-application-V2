from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80),  unique=True, nullable=False, index=True)
    email= db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20),  nullable=False, default='user')   # admin | staff | user
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(300))
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    status = db.Column(db.String(20), nullable=False, default='active') # active | blacklisted | inactive
    created_at = db.Column(db.DateTime, default=utcnow)

     # one-to-one relationship
    trekker_info = db.relationship('TrekkerInfo', back_populates='user', uselist=False, cascade='all, delete-orphan')
    staff_info   = db.relationship('StaffInfo',   back_populates='user', uselist=False, cascade='all, delete-orphan')
    
     # one-to-many relationship
    assigned_treks = db.relationship('Trek',         backref='assigned_staff', lazy='dynamic', foreign_keys='Trek.staff_id')
    bookings       = db.relationship('Booking',      backref='user', lazy='dynamic')
    reviews        = db.relationship('Review',       backref='user', lazy='dynamic')
    wishlist       = db.relationship('Wishlist',     backref='user', lazy='dynamic')
    notifications  = db.relationship('Notification', backref='user', lazy='dynamic')


    def get_name(self):
        return self.name or self.username

    def set_password(self, raw):
        self.password = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password, raw)
    
    def to_dict(self, full=False):
        d = {
            'id':             self.id,
            'name':           self.name,
            'username':       self.username,
            'email':          self.email,
            'role':           self.role,
            'status':         self.status,
            'phone':          self.phone,
            'bio':            self.bio,
            'avatar_url':     self.avatar_url,
            'created_at':     self.created_at.isoformat() if self.created_at else None,
            'total_bookings': self.bookings.count(),
        }
        if full:
            if self.trekker_info: d['trekker_info'] = self.trekker_info.to_dict()
            if self.staff_info:   d['staff_info']   = self.staff_info.to_dict()
        return d


class TrekkerInfo(db.Model):
    __tablename__ = 'trekker_info'
    id                   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id              = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    experience_level     = db.Column(db.String(20), default='Beginner')    # Beginner | Intermediate | Expert
    fitness_level        = db.Column(db.String(20), default='Medium')      # Low | Medium | High
    preferred_difficulty = db.Column(db.String(20))                        # Easy | Moderate | Hard
    emergency_contact    = db.Column(db.String(100))
    emergency_phone      = db.Column(db.String(20))
    medical_notes        = db.Column(db.Text)
    user = db.relationship('User', back_populates='trekker_info')

    def to_dict(self):
        completed = Booking.query.filter_by(
            user_id=self.user_id, status='Completed'
        ).count()
        return {
            'experience_level':     self.experience_level,
            'fitness_level':        self.fitness_level,
            'preferred_difficulty': self.preferred_difficulty,
            'emergency_contact':    self.emergency_contact,
            'emergency_phone':      self.emergency_phone,
            'medical_notes':        self.medical_notes,
            'total_trek_done':      completed
        }



class StaffInfo(db.Model):
    __tablename__ = 'staff_info'
    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    specialization   = db.Column(db.String(100))   # High Altitude | Winter | Forest | Desert
    certification    = db.Column(db.Text)
    years_experience = db.Column(db.Integer, default=0)
    language         = db.Column(db.String(200))   # comma-separated: Hindi, English, Nepali
    user = db.relationship('User', back_populates='staff_info')

    def to_dict(self):
        treks_led = Trek.query.filter_by(
            staff_id=self.user_id, status='Completed'
        ).count()
        return {
            'specialization':   self.specialization,
            'certification':    self.certification,
            'years_experience': self.years_experience,
            'language':         self.language,
            'treks_led':        treks_led,
        }


class Trek(db.Model):
    __tablename__ = 'treks'
    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name             = db.Column(db.String(200), nullable=False)
    location         = db.Column(db.String(200), nullable=False, index=True)
    difficulty       = db.Column(db.String(20),  nullable=False, index=True)   # Easy | Moderate | Hard
    duration         = db.Column(db.Integer, nullable=False)                    # in days
    total_slots      = db.Column(db.Integer, nullable=False)
    available_slots  = db.Column(db.Integer, nullable=False)
    staff_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status           = db.Column(db.String(20), default='Pending', index=True)  # Pending|Approved|Open|Closed|Completed
    start_date       = db.Column(db.Date,  nullable=True)
    end_date         = db.Column(db.Date,  nullable=True)
    description      = db.Column(db.Text)
    highlights       = db.Column(db.Text)        # pipe-separated  e.g. "Sunrise view|River crossing"
    included         = db.Column(db.Text)        # pipe-separated
    not_included     = db.Column(db.Text)        # pipe-separated
    image_url        = db.Column(db.String(300))
    altitude         = db.Column(db.Integer)     # in metres
    price            = db.Column(db.Float, default=0.0)
    meeting_point    = db.Column(db.String(300))
    equipment_needed = db.Column(db.Text)
    created_at       = db.Column(db.DateTime, default=utcnow)
    updated_at       = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    bookings = db.relationship('Booking',  backref='trek', lazy='dynamic')
    reviews  = db.relationship('Review',   backref='trek', lazy='dynamic')
    wishlist = db.relationship('Wishlist', backref='trek', lazy='dynamic')


    def avg_rating(self):
        from sqlalchemy import func
        res = db.session.query(func.avg(Review.rating)).filter(Review.trek_id == self.id).scalar()
        return round(res, 1) if res is not None else 0
    

    def to_dict(self):
        staff    = self.assigned_staff
        staff_si = staff.staff_info if staff else None
        return {
            'id':           self.id,
            'name':         self.name,
            'location':     self.location,
            'difficulty':   self.difficulty,
            'duration':     self.duration,
            'total_slots':      self.total_slots,
            'available_slots':  self.available_slots,
            'staff_id':                self.staff_id,
            'staff_name':              staff.name if staff else None,
            'staff_phone':             staff.phone if staff else None,
            'staff_email':             staff.email if staff else None,
            'staff_specialization':    staff_si.specialization   if staff_si else None,
            'staff_years_exp':         staff_si.years_experience if staff_si else None,
            'staff_languages':         staff_si.language         if staff_si else None,
            'status':     self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date':   self.end_date.isoformat()   if self.end_date   else None,
            'description':      self.description,
            'highlights':       self.highlights,
            'included':         self.included,
            'not_included':     self.not_included,
            'image_url':        self.image_url,
            'altitude':         self.altitude,
            'price':            self.price,
            'meeting_point':    self.meeting_point,
            'equipment_needed': self.equipment_needed,
            'booked_count':     self.bookings.filter_by(status='Booked').count(),
            'avg_rating':       self.avg_rating(),
            'review_count':     self.reviews.count(),
            'created_at':       self.created_at.isoformat() if self.created_at else None,
        }



class Booking(db.Model):
    __tablename__ = 'bookings'
    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id        = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    booking_date   = db.Column(db.DateTime, default=utcnow)
    status         = db.Column(db.String(20), default='Booked')    # Booked | Cancelled | Completed
    payment_status = db.Column(db.String(20), default='Pending')   # Pending | Paid | Refunded
    payment_method = db.Column(db.String(30))
    transaction_id = db.Column(db.String(50))
    amount         = db.Column(db.Float, default=0.0)
    notes          = db.Column(db.Text)
    updated_at     = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self):
        t = self.trek
        u = self.user
        reviewed = Review.query.filter_by(
            user_id=self.user_id, trek_id=self.trek_id
        ).first()
        staff = t.assigned_staff if t else None
        return {
            'id':              self.id,
            'user_id':         self.user_id,
            'user_name':       u.get_name() if u else None,
            'user_email':      u.email      if u else None,
            'trek_id':         self.trek_id,
            'trek_name':       t.name       if t else None,
            'trek_location':   t.location   if t else None,
            'trek_difficulty': t.difficulty if t else None,
            'trek_status':     t.status     if t else None,
            'booking_date':    self.booking_date.isoformat() if self.booking_date else None,
            'status':          self.status,
            'payment_status':  self.payment_status,
            'payment_method':  self.payment_method,
            'transaction_id':  self.transaction_id,
            'amount':          self.amount,
            'notes':           self.notes,
            'start_date':      t.start_date.isoformat() if t and t.start_date else None,
            'end_date':        t.end_date.isoformat()   if t and t.end_date   else None,
            'reviewed':        reviewed is not None,
            'review_id':       reviewed.id if reviewed else None,
            'staff_name':      staff.name if staff else 'Unassigned',
            'staff_phone':     staff.phone if staff else None,
            'staff_email':     staff.email if staff else None,
        }


   
class Review(db.Model):
    __tablename__ = 'reviews'
    __table_args__ = (db.UniqueConstraint('user_id', 'trek_id', name='uq_user_trek_review'),)
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id    = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    rating     = db.Column(db.Integer, nullable=False)   # 1–5
    comment    = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        u = self.user
        t = self.trek
        return {
            'id':         self.id,
            'user_id':    self.user_id,
            'trek_id':    self.trek_id,
            'user_name':  u.get_name() if u else None,
            'trek_name':  t.name       if t else None,
            'rating':     self.rating,
            'comment':    self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    __table_args__ = (db.UniqueConstraint('user_id', 'trek_id', name='uq_wishlist'),)
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id    = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        t = self.trek
        return {
            'id':            self.id,
            'trek_id':       self.trek_id,
            'trek_name':     t.name       if t else None,
            'trek_location': t.location   if t else None,
            'created_at':    self.created_at.isoformat() if self.created_at else None,
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title      = db.Column(db.String(200), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    type       = db.Column(db.String(20), default='info')   # info | success | warning | danger
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            'id':         self.id,
            'user_id':    self.user_id,
            'title':      self.title,
            'message':    self.message,
            'type':       self.type,
            'is_read':    self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
