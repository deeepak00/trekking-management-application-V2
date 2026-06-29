from flask import Flask
from flask_cors import CORS
from config import Config, LocalConfig
from extensions import db, jwt
from models.models import User, TrekkerInfo, StaffInfo, Trek


app = None
def create_app():
    app = Flask(__name__)
    app.config.from_object(LocalConfig)
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r'/api/*': {'origins': '*'}})
    app.app_context().push()
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
        admin.set_password("admin@123")
        db.session.add(admin)
        db.session.commit()
    
app = create_app()

if __name__ == "__main__":
    db.create_all()
    create_admin()
    app.run()

