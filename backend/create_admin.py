#!/usr/bin/env python3
"""
Script to create an admin user for the Purposeful Live platform.
Run this script to create the first admin user.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, UserRole
import getpass

def create_admin_user():
    app = create_app()
    
    with app.app_context():
        print("Creating admin user for Purposeful Live...")
        
        email = input("Admin email: ")
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"User with email {email} already exists!")
            return
        
        first_name = input("First name: ")
        last_name = input("Last name: ")
        password = getpass.getpass("Password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            print("Passwords don't match!")
            return
        
        admin_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN
        )
        admin_user.set_password(password)
        
        db.session.add(admin_user)
        db.session.commit()
        
        print(f"Admin user created successfully!")
        print(f"Email: {email}")
        print(f"Role: {admin_user.role.value}")

if __name__ == "__main__":
    create_admin_user()
