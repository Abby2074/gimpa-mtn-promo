"""
GIMPA × MTN 10GB Free Data Promo — Academic Baiting Awareness Project
=====================================================================

This Flask web application simulates a fake "GIMPA × MTN 10GB Free Data"
promotion to educate students about baiting attacks in cybersecurity.

HOW TO RUN
----------
1. Install dependencies:
       pip install flask flask-sqlalchemy

2. Run the app (PORT and FLASK_DEBUG can be set via environment):
       python app.py

3. Open http://127.0.0.1:5000 in your browser (default port 5000).

4. Admin dashboard:
       URL:      http://127.0.0.1:5000/admin/login
       Username: admin
       Password: admin123

The SQLite database (promo.db) is created automatically on first run.
"""

import os
import hashlib
import secrets
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from flask_sqlalchemy import SQLAlchemy

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
# Use environment-provided secrets/config in development/production
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "gimpa-mtn-project-secret-key-change-in-production",
)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///promo.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

# Hard-coded admin credentials (for academic use only)
ADMIN_USERNAME = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASS", "admin123")

db = SQLAlchemy(app)

# ---------------------------------------------------------------------------
# Database models
# ---------------------------------------------------------------------------

class ClickEvent(db.Model):
    """
    Records every click on the 'Register Now' button on the landing page.
    This lets the admin see how many people were tempted by the fake offer.
    """
    __tablename__ = "click_events"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45), nullable=True)   # IPv4 or IPv6
    user_agent = db.Column(db.String(512), nullable=True)
    source = db.Column(db.String(50), default="unknown")    # e.g. poster, whatsapp


class Submission(db.Model):
    """
    Stores the personal details a student submits on the registration form.
    The national_id is hashed before storage to demonstrate responsible
    handling — in a real attack, the attacker would keep it in plain text.
    """
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    school_email = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    school_id = db.Column(db.String(50), nullable=False)
    # Plain national ID (stored as provided). WARNING: storing raw IDs is
    # insecure. This app intentionally exposes it for demonstration/testing
    # because the user requested the national ID to be visible in the
    # dashboard. Keep for local/dev only.
    national_id = db.Column(db.String(100), nullable=True)
    national_id_hash = db.Column(db.String(64), nullable=False)  # SHA-256 hash
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    source = db.Column(db.String(50), default="unknown")
    user_agent = db.Column(db.String(512), nullable=True)

# ---------------------------------------------------------------------------
# Helper: hash the national ID so we never store the raw value
# ---------------------------------------------------------------------------


def hash_national_id(raw_id: str) -> str:
    """Return a SHA-256 hex digest of the national ID string."""
    return hashlib.sha256(raw_id.strip().encode("utf-8")).hexdigest()


def ensure_csrf_token():
    """Create or return the per-session CSRF token."""
    token = session.get("csrf_token")
    if not token:
        token = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
        session["csrf_token"] = token
    return token

# ---------------------------------------------------------------------------
# Helper: require admin login
# ---------------------------------------------------------------------------


def admin_required(f):
    """Decorator that redirects to /admin/login if the user is not logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please log in to access the dashboard.", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)

    return decorated

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

# --- Landing page -----------------------------------------------------------


@app.route("/")
def landing():
    """
    GET /
    Shows the fake GIMPA × MTN promo landing page.
    The ?src= query parameter is passed along so we can track the source.
    """
    source = request.args.get("src", "unknown")
    return render_template("landing.html", source=source)


# --- Log click and redirect to form ----------------------------------------


@app.route("/click")
def log_click():
    """
    GET /click?src=...
    Called when the user clicks 'Register Now'.
    1. Logs the click event into the database.
    2. Redirects the user to the registration form.
    """
    source = request.args.get("src", "unknown")

    event = ClickEvent(
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent", ""),
        source=source,
    )
    db.session.add(event)
    db.session.commit()

    return redirect(url_for("form_page", src=source))


# --- Registration form ------------------------------------------------------


@app.route("/form", methods=["GET"])
def form_page():
    """
    GET /form
    Displays the registration form that collects student details.
    """
    source = request.args.get("src", "unknown")
    csrf = ensure_csrf_token()
    return render_template("form.html", source=source, csrf_token=csrf)


@app.route("/submit-form", methods=["POST"])
def submit_form():
    """
    POST /submit-form
    Processes the registration form submission:
    1. Validates that all fields are filled.
    2. Hashes the national ID for safe storage.
    3. Saves the submission to the database.
    4. Redirects to the reveal / education page.
    """
    # Read form fields
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    school_email = request.form.get("school_email", "").strip()
    phone_number = request.form.get("phone_number", "").strip()
    school_id = request.form.get("school_id", "").strip()
    national_id = request.form.get("national_id", "").strip()
    source = request.form.get("source", "unknown")

    # CSRF check
    form_csrf = request.form.get("csrf_token")
    if not form_csrf or form_csrf != session.get("csrf_token"):
        flash("Invalid session. Please refresh the form and try again.", "error")
        return redirect(url_for("form_page", src=source))

    # Simple server-side validation: all fields required
    if not all([first_name, last_name, school_email, phone_number, school_id, national_id]):
        flash("All fields are required. Please fill in every field.", "error")
        return redirect(url_for("form_page", src=source))

    # Save submission
    submission = Submission(
        first_name=first_name,
        last_name=last_name,
        school_email=school_email,
        phone_number=phone_number,
        school_id=school_id,
        national_id=national_id,
        national_id_hash=hash_national_id(national_id),
        source=source,
        user_agent=request.headers.get("User-Agent", ""),
    )
    db.session.add(submission)
    db.session.commit()

    return redirect(url_for("info_page"))


# --- Reveal / education page ------------------------------------------------


@app.route("/info")
def info_page():
    """
    GET /info
    Reveals to the user that the promotion was fake and educates them
    about baiting attacks, red flags, and how to stay safe.
    """
    return render_template("info.html")


# --- Admin login -------------------------------------------------------------


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """
    GET  /admin/login — shows the login form.
    POST /admin/login — checks credentials and sets a session flag.
    """
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # CSRF check for login form
        form_csrf = request.form.get("csrf_token")
        if not form_csrf or form_csrf != session.get("csrf_token"):
            flash("Invalid session. Please refresh and try again.", "error")
            return redirect(url_for("admin_login"))

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid username or password.", "error")

    # Ensure CSRF token is present for the login form
    csrf = ensure_csrf_token()
    return render_template("admin_login.html", csrf_token=csrf)


@app.route("/admin/logout")
def admin_logout():
    """Clears the admin session and redirects to the login page."""
    session.pop("admin_logged_in", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("admin_login"))


# --- Admin dashboard ---------------------------------------------------------


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """
    GET /admin/dashboard  (admin-only)
    Shows key metrics, a summary table, and the list of submissions.
    """
    # Counts
    total_clicks = ClickEvent.query.count()
    total_submissions = Submission.query.count()
    conversion_rate = (
        round((total_submissions / total_clicks) * 100, 1)
        if total_clicks > 0 else 0
    )

    # Clicks by source
    source_counts = (
        db.session.query(ClickEvent.source, db.func.count(ClickEvent.id))
        .group_by(ClickEvent.source)
        .all()
    )

    # Submissions by day (for a simple chart)
    daily_submissions = (
        db.session.query(
            db.func.date(Submission.created_at).label("day"),
            db.func.count(Submission.id).label("count"),
        )
        .group_by("day")
        .order_by("day")
        .all()
    )

    # All submissions for the detailed table
    submissions = Submission.query.order_by(Submission.created_at.desc()).all()

    return render_template(
        "admin_dashboard.html",
        total_clicks=total_clicks,
        total_submissions=total_submissions,
        conversion_rate=conversion_rate,
        source_counts=source_counts,
        daily_submissions=daily_submissions,
        submissions=submissions,
    )


# ---------------------------------------------------------------------------
# Create tables and run the app
# ---------------------------------------------------------------------------

with app.app_context():
    # Create tables if they don't exist
    db.create_all()

    # Ensure the `national_id` column exists in the `submissions` table.
    # SQLite supports ADD COLUMN; if the column is missing, add it so older
    # databases are upgraded in-place.
    try:
        from sqlalchemy import inspect, text

        inspector = inspect(db.engine)
        cols = [c['name'] for c in inspector.get_columns('submissions')]
        if 'national_id' not in cols:
            # Add a nullable text column for plain national ID using session.execute
            db.session.execute(text('ALTER TABLE submissions ADD COLUMN national_id VARCHAR'))
            db.session.commit()
    except Exception:
        # If anything fails here, we don't want to crash the app on startup.
        # The admin can still add the column manually or recreate the DB.
        pass


if __name__ == "__main__":
    # Run on all interfaces so it's accessible on the local network
    app.run(
        debug=app.config.get("DEBUG", False),
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
    )
