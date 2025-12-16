"""
SQLite Database Setup for Authentication
Creates users table with default admin user
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "auth.db")

def init_db():
    """Initialize SQLite database with users table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def create_default_user():
    """Create default admin user if not exists"""
    from werkzeug.security import generate_password_hash
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if admin user exists
    cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@productx.com",))
    user = cursor.fetchone()
    
    if not user:
        # Create default user: email=admin@productx.com, password=admin123
        password_hash = generate_password_hash("admin123")
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            ("admin@productx.com", password_hash)
        )
        conn.commit()
        print("[OK] Default user created: admin@productx.com / admin123")
    else:
        print("[OK] Default user already exists")
    
    conn.close()

def verify_password(email: str, password: str) -> bool:
    """Verify user credentials"""
    from werkzeug.security import check_password_hash
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return False
    
    return check_password_hash(result[0], password)

def get_user(email: str):
    """Get user by email"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, email FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {"id": result[0], "email": result[1]}
    return None

# Initialize on import
if not os.path.exists(DB_PATH):
    init_db()
    create_default_user()
