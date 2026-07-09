from flask import Flask
from flask_cors import CORS
from config import Config, LocalConfig
from extensions import db, jwt, cache, mail
from models.models import User, TrekkerInfo, StaffInfo, Trek, Booking, Review, Wishlist, Notification
from jobs import init_scheduler

try:
    import redis
except ImportError:
    redis = None

app = None

def create_app():
    app = Flask(__name__)
    app.config.from_object(LocalConfig)
    
    if redis is not None:
        try:
            r = redis.Redis.from_url(app.config.get('CACHE_REDIS_URL', 'redis://127.0.0.1:6379/0'), socket_connect_timeout=1)
            r.ping()
            print("[TMA Cache] Redis is available. Using RedisCache.")
        except Exception:
            print("[TMA Cache] Redis is not available or connection failed. Falling back to SimpleCache.")
            app.config['CACHE_TYPE'] = 'SimpleCache'
    else:
        print("[TMA Cache] Redis package is not installed. Falling back to SimpleCache.")
        app.config['CACHE_TYPE'] = 'SimpleCache'
        
    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    CORS(app, resources={r'/api/*': {'origins': '*'}})
    
    app.app_context().push()
    
    db.create_all()
    create_admin()
    
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.staff import staff_bp
    from routes.user import trekker_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(staff_bp, url_prefix='/api/staff')
    app.register_blueprint(trekker_bp, url_prefix='/api/trekker')
    
    init_scheduler(app)
    
    return app

def create_admin():
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username='admin',
            email='admin@gmail.com',
            role='admin',
            name='Admin',
            phone='+91-9000000000',
            bio='System Administrator'
        )
        admin.set_password("Admin@123")
        db.session.add(admin)
        db.session.commit()
        print("[TMA App] Programmatic admin account 'admin' created successfully.")

app = create_app()

if __name__ == "__main__":
    app.run()
