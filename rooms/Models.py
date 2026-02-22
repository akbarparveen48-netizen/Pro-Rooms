"""
rooms/Models.py
───────────────
SQLAlchemy ORM models (PostgreSQL) and a raw psycopg2 connection helper.
"""

import os
from datetime import datetime

import psycopg2
import psycopg2.extras
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

# ── SQLAlchemy instance (shared with app.py) ──────────────────────────────────
db = SQLAlchemy()


# ── Raw psycopg2 connection (used for direct queries in routes) ───────────────
def get_db_connection():
    """
    Return a live psycopg2 connection to the PostgreSQL database.
    Credentials are read from environment variables:
        DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST",     "localhost"),
        port=os.getenv("DB_PORT",     "5432"),
        user=os.getenv("DB_USER",     "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        dbname=os.getenv("DB_NAME",   "rooms_db")
    )


# ── ORM Models ────────────────────────────────────────────────────────────────

class SSO_User(db.Model):
    """Stores users who sign in via Google OAuth."""

    __tablename__ = "sso_users"

    id        = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email     = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name      = db.Column(db.String(255), nullable=False)
    picture   = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

    def __repr__(self):
        return f"<SSO_User {self.email}>"

    def to_dict(self):
        return {
            "id":         self.id,
            "google_id":  self.google_id,
            "email":      self.email,
            "name":       self.name,
            "picture":    self.picture,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class User(db.Model):
    """Stores users who register with username/email/password."""

    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password   = db.Column(db.String(255), nullable=False)   # SHA-256 hex digest
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"


class Room(db.Model):
    """Stores information about student/pro rooms (WhatsApp group links)."""

    __tablename__ = "rooms"

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    description   = db.Column(db.Text, nullable=True)
    whatsapp_link = db.Column(db.String(500), nullable=False)
    password      = db.Column(db.String(6), nullable=False)  # 6-digit password
    # Linking to users is tricky since we have two types. 
    # For now, we'll store creator_info as a string or use two optional FKs.
    creator_id    = db.Column(db.Integer, nullable=False)
    creator_type  = db.Column(db.String(20), nullable=False) # 'local' or 'sso'
    created_at    = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id":          self.id,
            "name":        self.name,
            "description": self.description,
            "created_at":  self.created_at.isoformat(),
            "creator_type": self.creator_type
        }
