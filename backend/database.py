from models import db
import os

def init_database(app):
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///purposeful_live.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
