"""
app.py
──────
Pro-Rooms Flask application entry-point.

Routes:
    GET  /  or  /login   → Login page
    POST /login           → Authenticate local user
    GET  /signup          → Registration page
    POST /signup          → Create new local user
    GET  /auth/google     → Redirect to Google OAuth
    GET  /auth/google/callback → Process Google OAuth token
    GET  /dashboard       → Main chat page (auth required)
    GET  /logout          → Clear session
"""

import hashlib
import secrets

import psycopg2
import psycopg2.extras
from authlib.integrations.base_client.errors import OAuthError
from datetime import datetime
from dotenv import load_dotenv
from flask import (
    Flask, flash, jsonify, redirect,
    render_template, request, session, url_for
)

from rooms.Config import Config, init_oauth
from rooms.Models import db, get_db_connection, User, SSO_User, Room

# ── App Initialisation ────────────────────────────────────────────────────────
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
Config.validate()

app.secret_key = Config.SECRET_KEY

# Initialise SQLAlchemy (ORM – used for SSO_User / User tables)
db.init_app(app)

# Initialise Google OAuth
oauth  = init_oauth(app)
google = oauth.google


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle local username/email + password login."""
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password   = request.form.get("password",   "").strip()

        if not identifier or not password:
            flash("Please enter your username/email and password ❗", "error")
            return redirect(url_for("login"))

        conn = cursor = None
        try:
            conn   = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cursor.execute(
                "SELECT * FROM users WHERE username = %s OR email = %s",
                (identifier, identifier)
            )
            user = cursor.fetchone()

            if not user:
                flash("No account found with that username or email 📧", "error")
                return redirect(url_for("login"))

            hashed_input = hashlib.sha256(password.encode()).hexdigest()
            if hashed_input == user["password"]:
                session["user_id"]  = user["id"]
                session["username"] = user["username"]
                flash(f"Welcome back, {user['username']} 👋", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Incorrect password ❌", "error")

        except psycopg2.Error as err:
            flash(f"Database error: {err}", "error")
        finally:
            if cursor: cursor.close()
            if conn:   conn.close()

    return render_template("login.html")


# ─────────────────────────────────────────────────────────────────────────────
# SIGNUP
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Handle new user registration."""
    if request.method == "POST":
        username   = request.form.get("username",        "").strip()
        email      = request.form.get("email",           "").strip()
        password   = request.form.get("password",        "").strip()
        c_password = request.form.get("ConfirmPassword", "").strip()

        if not username or not email or not password:
            flash("All fields are required ❗", "error")
            return redirect(url_for("signup"))

        if password != c_password:
            flash("Passwords do not match ⚠️", "error")
            return redirect(url_for("signup", username=username, email=email))

        conn = cursor = None
        try:
            conn   = get_db_connection()
            cursor = conn.cursor()

            hashed = hashlib.sha256(password.encode()).hexdigest()

            # PostgreSQL SERIAL handles auto-increment; no manual ID needed.
            cursor.execute(
    "INSERT INTO users (username, email, password, created_at) VALUES (%s, %s, %s, %s)",
    (username, email, hashed, datetime.utcnow())
)
            conn.commit()

            flash("Account created successfully ✅ Please log in.", "success")
            return redirect(url_for("login"))

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash("An account with that email already exists 📧", "error")
            return redirect(url_for("signup", username=username))
        except psycopg2.Error as err:
            if conn: conn.rollback()
            flash(f"Database error: {err}", "error")
        finally:
            if cursor: cursor.close()
            if conn:   conn.close()

    username = request.args.get("username", "")
    email    = request.args.get("email",    "")
    return render_template("signup.html", username=username, email=email)


# ─────────────────────────────────────────────────────────────────────────────
# GOOGLE OAUTH
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/auth/google")
def google_login():
    """Redirect user to Google's OAuth consent screen."""
    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/auth/google/callback")
def google_callback():
    """Process the token returned by Google and create/update the user record."""
    try:
        token     = google.authorize_access_token()
        user_info = token.get("userinfo")

        if not user_info:
            flash("Failed to fetch user info from Google 😞", "error")
            return redirect(url_for("login"))

        google_id = user_info.get("sub")
        email     = user_info.get("email")
        name      = user_info.get("name")
        picture   = user_info.get("picture")

        user = SSO_User.query.filter_by(google_id=google_id).first()

        if user:
            # Returning user – update profile snapshot
            user.last_login = datetime.utcnow()
            user.name       = name
            user.picture    = picture
            db.session.commit()

            session["user_id"]    = user.id
            session["user_email"] = user.email
            session["is_new_user"] = False
            flash(f"Welcome back, {user.name}! 👋", "success")

        else:
            # First sign-in – create record
            new_user = SSO_User(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
            )
            db.session.add(new_user)
            db.session.commit()

            session["user_id"]    = new_user.id
            session["user_email"] = new_user.email
            session["is_new_user"] = True
            flash(f"Welcome to Pro Rooms, {new_user.name}! 🎉", "success")

        return redirect(url_for("dashboard"))

    except OAuthError as e:
        flash(f"OAuth error: {str(e)}", "error")
        return redirect(url_for("login"))
    except Exception as e:
        print(f"[google_callback] Unexpected error: {e}")
        flash(f"Authentication failed: {str(e)}", "error")
        return redirect(url_for("login"))


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    """Main dashboard page."""
    if "user_id" not in session:
        flash("Please log in first ❗", "error")
        return redirect(url_for("login"))
    
    # Get initial list of rooms
    rooms = Room.query.order_by(Room.created_at.desc()).all()
    return render_template("index.html", rooms=rooms)


# ── Room API ──────────────────────────────────────────────────────────────────

@app.route("/api/rooms", methods=["GET"])
def get_rooms():
    """Fetch rooms with search and filtering."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    search_query = request.args.get("search", "").strip()
    
    query = Room.query
    if search_query:
        query = query.filter(Room.name.ilike(f"%{search_query}%") | 
                           Room.description.ilike(f"%{search_query}%"))
    
    rooms = query.order_by(Room.created_at.desc()).all()
    return jsonify([room.to_dict() for room in rooms])


@app.route("/api/rooms", methods=["POST"])
def create_room():
    """Create a new room."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid data"}), 400
    
    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    whatsapp_link = data.get("whatsapp_link", "").strip()
    password = data.get("password", "").strip()
    
    if not all([name, whatsapp_link, password]):
        return jsonify({"error": "Missing required fields"}), 400
    
    if len(password) != 6 or not password.isdigit():
        return jsonify({"error": "Password must be a 6-digit number"}), 400

    # Determine creator type (this is a bit of a hack since session structure differs)
    # If session has 'username', it's likely a local user.
    creator_type = "local" if "username" in session else "sso"
    
    try:
        new_room = Room(
            name=name,
            description=description,
            whatsapp_link=whatsapp_link,
            password=password,
            creator_id=session["user_id"],
            creator_type=creator_type
        )
        db.session.add(new_room)
        db.session.commit()
        return jsonify({"success": True, "room": new_room.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/rooms/join", methods=["POST"])
def join_room():
    """Verify password and return WhatsApp link."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    room_id = data.get("room_id")
    password = data.get("password", "").strip()
    
    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
        
    if room.password == password:
        return jsonify({"success": True, "link": room.whatsapp_link})
    else:
        return jsonify({"error": "Incorrect password"}), 403


# ─────────────────────────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully 👋", "success")
    return redirect(url_for("login"))


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ PostgreSQL tables created / verified.")
    app.run(port=5000, debug=True)
