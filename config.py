import os
from datetime import datetime

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'luxury-wellness-spa-secret-key-2024'
    
    # Use absolute path for SQLite database
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "database", "site.db")}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WHATSAPP_NUMBER = '+9170390080000'  # Replace with actual number
    SPA_NAME = 'Travaa Wellness Spa & Nail Art'
    INSTAGRAM_USERNAME = 'travaawellness'