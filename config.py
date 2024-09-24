import os
from datetime import timedelta

class Config:
    # General Flask Configurations
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default_secret_key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or '217ef16e1e9a07be79a7a4d9e3f20d027a3a274ad4dc215d582aca4d7a1a15d2'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)

    # Cloudinary Configuration
    CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL') or 'cloudinary://456584813683358:N70vCZCBhr1dSsTVw_TFch6Euwt@dqfbde8ib'

    # M-Pesa Configuration
    MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY') or 'SPzneIGYRgzWGO5B9CXINWjWa3nx9YE0sOisQFshwEIXEHqF'
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET') or 'agaKNaGcKWf3DLgJGGRVmuDCewsNWejGVd5mMws1UwACij8DYHaNeGKnwv6AcAKT'
    MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE') or 'N/A'
    MPESA_LIPA_SHORTCODE = os.environ.get('MPESA_LIPA_SHORTCODE') or 'N/A'
    MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY') or 'N/A'
    MPESA_ENVIRONMENT = os.environ.get('MPESA_ENVIRONMENT') or 'sandbox'

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://agriconnect_hxov_user:hYGLluhLlxLik1w8WsGMG7LDqJaxq6BU@dpg-crp5r4tds78s73d4o520-a.oregon-postgres.render.com/agriconnect_hxov'
class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
