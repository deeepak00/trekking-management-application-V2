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


    def set_password(self, raw):
        self.password = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password, raw)


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



class StaffInfo(db.Model):
    __tablename__ = 'staff_info'
    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    specialization   = db.Column(db.String(100))   # High Altitude | Winter | Forest | Desert
    certification    = db.Column(db.Text)
    years_experience = db.Column(db.Integer, default=0)
    language         = db.Column(db.String(200))   # comma-separated: Hindi, English, Nepali
    user = db.relationship('User', back_populates='staff_info')


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
    min_age          = db.Column(db.Integer, default=10)
    max_age          = db.Column(db.Integer, default=65)
    created_at       = db.Column(db.DateTime, default=utcnow)
    updated_at       = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    bookings = db.relationship('Booking',  backref='trek', lazy='dynamic')
    reviews  = db.relationship('Review',   backref='trek', lazy='dynamic')
    wishlist = db.relationship('Wishlist', backref='trek', lazy='dynamic')


    def avg_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)



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

   
class Review(db.Model):
    __tablename__ = 'reviews'
    __table_args__ = (db.UniqueConstraint('user_id', 'trek_id', name='uq_user_trek_review'),)
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id    = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    rating     = db.Column(db.Integer, nullable=False)   # 1–5
    comment    = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)


class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    __table_args__ = (db.UniqueConstraint('user_id', 'trek_id', name='uq_wishlist'),)
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id    = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)


class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title      = db.Column(db.String(200), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    type       = db.Column(db.String(20), default='info')   # info | success | warning | danger
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)
