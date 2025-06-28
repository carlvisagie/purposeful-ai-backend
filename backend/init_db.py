#!/usr/bin/env python3
"""
Database initialization script for Purposeful Live AI Coaching Platform
Creates the database schema and initial admin user
"""

import os
import sys
from flask import Flask
from flask_migrate import init, migrate, upgrade
from models import db, User, UserRole
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def init_database():
    """Initialize the database with schema and initial data"""
    app = create_app()
    
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully")
            
            admin_user = User.query.filter_by(email='admin@purposefullive.com').first()
            
            if not admin_user:
                admin_user = User(
                    email='admin@purposefullive.com',
                    first_name='System',
                    last_name='Administrator',
                    role=UserRole.ADMIN,
                    email_verified=True
                )
                admin_user.set_password('admin123!')  # Change this in production
                
                db.session.add(admin_user)
                db.session.commit()
                
                print("✅ Initial admin user created:")
                print("   Email: admin@purposefullive.com")
                print("   Password: admin123!")
                print("   ⚠️  CHANGE THE PASSWORD IN PRODUCTION!")
            else:
                print("✅ Admin user already exists")
            
            print("\n🎉 Database initialization completed successfully!")
            print("\nNext steps:")
            print("1. Set up your environment variables (see .env.example)")
            print("2. Configure PostgreSQL connection")
            print("3. Set up Stripe API keys")
            print("4. Configure email settings for crisis alerts")
            print("5. Start the Flask application")
            
        except Exception as e:
            print(f"❌ Database initialization failed: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    init_database()
