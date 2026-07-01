from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_caching import Cache



db = SQLAlchemy()
jwt = JWTManager()
cache = Cache()
mail  = Mail()



@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.username

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    from models.models import User
    identity = jwt_data['sub']
    return User.query.filter_by(username=identity).first()