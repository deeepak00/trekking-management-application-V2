class Config:
    DEBUG = False
    SECRET_KEY = 'tma-secret-key-fallback-key-at-least-32-bytes-long'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = 'super-secret-key-that-is-at-least-32-bytes-long'
    JWT_ACCESS_TOKEN_EXPIRES = 86400 

    # Flask-Mail configurations (Gmail SMTP setup)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = '23f3004133@ds.study.iitm.ac.in'
    MAIL_PASSWORD = 'gcggadrdqyrnyyze'
    MAIL_DEFAULT_SENDER = '23f3004133@ds.study.iitm.ac.in'
    
    # Admin notification recipient
    ADMIN_EMAIL = 'admin@gmail.com'

    # Flask-Caching Redis configuration
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = 'redis://127.0.0.1:6379/0'
    CACHE_DEFAULT_TIMEOUT = 300

class LocalConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///trekking.db'
