class Config:
    DEBUG = False
    SECRET_KEY = 'tma-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = 'jwt-tma-secret'
    JWT_ACCESS_TOKEN_EXPIRES = 86400 

class LocalConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///trekking.db'
    
