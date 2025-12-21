#!/usr/bin/env python3
"""
Create admin user script
"""
import sys
from database import get_db, init_db
from services.auth_service import AuthService
from utils.logger import logger

def create_admin(username: str, email: str, password: str):
    """Create an admin user"""
    init_db()
    db = next(get_db())
    try:
        user = AuthService.create_user(
            db=db,
            username=username,
            email=email,
            password=password
        )
        logger.info(f"Admin user '{username}' created successfully")
        return user
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python scripts/create_admin.py <username> <email> <password>")
        sys.exit(1)
    
    username, email, password = sys.argv[1], sys.argv[2], sys.argv[3]
    create_admin(username, email, password)
    print(f"Admin user '{username}' created successfully!")

