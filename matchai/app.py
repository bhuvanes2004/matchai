"""
MatchAI - AI-Powered Job Resume Matching Platform
Main Flask Application
"""

import os
import sqlite3
import re
from functools import wraps
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_from_directory
)

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "matchai-secret-key-change-in-production"
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

# ---------------------------------------------------------------------------
# Skill keyword bank used for extraction and matching
# ---------------------------------------------------------------------------
SKILL_KEYWORDS = [
    "python", "javascript", "java", "c++", "c#", "ruby", "go", "rust", "swift",
    "typescript", "php", "scala", "kotlin", "r", "matlab", "perl",
    "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
    "spring", "express", "laravel", "rails", "next.js", "nuxt.js",
    "html", "css", "sass", "less", "bootstrap", "tailwind",
    "sql", "nosql", "postgresql", "mysql", "mongodb", "redis", "sqlite",
    "docker", "kubernetes", "aws", "azure", "gcp", "terraform", "jenkins",
    "git", "github", "ci/cd", "linux", "nginx", "apache",
    "machine learning", "deep learning", "tensorflow", "pytorch",
    "scikit-learn", "pandas", "numpy", "scipy", "nlp", "computer vision",
    "data visualization", "tableau", "power bi", "excel", "statistics",
    "rest api", "graphql", "microservices", "agile", "scrum",
    "figma", "adobe xd", "photoshop", "illustrator", "sketch",
    "user research", "wireframing", "prototyping", "usability testing",
    "data analysis", "data science", "etl", "hadoop", "spark",
]

# ---------------------------------------------------------------------------
# Database Helper
# ---------------------------------------------------------------------------

def get_db():
    """Return a database connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Auth Decorator
# ---------------------------------------------------------------------------

def login_required(f):
    """Redirect to login if user not in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def role_required(role):
    """Restrict access to a specific role."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("login"))
            if session.get("role") != role:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("home"))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ---------------------------------------------------------------------------
# AI Matching Logic
# ---------------------------------------------------------------------------

def extract_skills_from_text(text):
    """Extract skills from text by matching against the keyword bank."""
    text_lower = text.lower()
    found = set()
    for skill in SKILL_KEYWORDS:
        # Use word-boundary-style matching to avoid false positives
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found.add(skill.title())
    return sorted(found)


def calculate_match_score(resume_skills_str, job_skills_str):
    """Calculate match percentage between resume skills and job skills."""
    if not job_skills_str or not resume_skills_str:
        return 0.0
    resume_skills = {s.strip().lower() for s in resume_skills_str.split(",") if s.strip()}
    job_skills = {s.strip().lower() for s in job_skills_str.split(",") if s.strip()}
    if not job_skills:
        return 0.0
    matched = resume_skills & job_skills
    score = (len(matched) / len(job_skills)) * 100
    return round(min(score, 100.0), 1)


def get_resume_skills(user_id):
    """Get extracted skills for a user's resume."""
    db = get_db()
    resume = db.execute("SELECT extracted_skills FROM resumes WHERE user_id = ?", (user_id,)).fetchone()
    db.close()
    return resume["extracted_skills"] if resume else ""


def calculate_profile_strength(user_id):
    """Calculate profile completeness percentage."""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    resume = db.execute("SELECT * FROM resumes WHERE user_id = ?", (user_id,)).fetchone()
    db.close()

    score = 0
    if user["name"]:
        score += 15
    if user["email"]:
        score += 10
    if user["phone"]:
        score += 10
    if user["location"]:
        score += 10
    if user["bio"]:
        score += 15
    if resume:
        score += 10
        if resume["extracted_skills"]:
            score += 15
        if resume["education"]:
            score += 10
        if resume["experience"]:
            score += 5
    return score


# ---------------------------------------------------------------------------
# PDF Text Extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(filepath):
    """Extract text content from a PDF file."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""


# ---------------------------------------------------------------------------
# Context Processor – inject notification count into every template
# ---------------------------------------------------------------------------

@app.context_processor
def inject_notifications():
    if "user_id" in session:
        db = get_db()
        count = db.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
            (session["user_id"],),
        ).fetchone()[0]
        db.close()
        return {"unread_notifications": count}
    return {"unread_notifications": 0}


# ---------------------------------------------------------------------------
# Public Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    """Landing page."""
    db = get_db()
    stats = {
        "jobs": db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
        "candidates": db.execute("SELECT COUNT(*) FROM users WHERE role = 'candidate'").fetchone()[0],
        "recruiters": db.execute("SELECT COUNT(*) FROM users WHERE role = 'recruiter'").fetchone()[0],
        "applications": db.execute("SELECT COUNT(*) FROM applications").fetchone()[0],
    }
    recent_jobs = db.execute(
        "SELECT j.*, u.name as recruiter_name FROM jobs j JOIN users u ON j.recruiter_id = u.id ORDER BY j.created_at DESC LIMIT 6"
    ).fetchall()
    db.close()
    return render_template("home.html", stats=stats, recent_jobs=recent_jobs)


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['name']}!", "success")
            if user["role"] == "recruiter":
                return redirect(url_for("recruiter_dashboard"))
            return redirect(url_for("candidate_dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        role = request.form.get("role", "candidate")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash("Email already registered.", "danger")
            db.close()
            return render_template("register.html")

        hashed = generate_password_hash(password)
        cursor = db.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?,?,?,?)",
            (name, email, hashed, role),
        )
        db.commit()

        session["user_id"] = cursor.lastrowid
        session["name"] = name
        session["email"] = email
        session["role"] = role
        db.close()
        flash("Account created successfully!", "success")
        if role == "recruiter":
            return redirect(url_for("recruiter_dashboard"))
        return redirect(url_for("candidate_dashboard"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    """Log out the current user."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# Job Routes (Public)
# ---------------------------------------------------------------------------

@app.route("/jobs")
def job_listings():
    """Browse all job openings with optional search/filter."""
    search = request.args.get("search", "").strip()
    location = request.args.get("location", "").strip()
    job_type = request.args.get("job_type", "").strip()

    db = get_db()
    query = "SELECT j.*, u.name as recruiter_name FROM jobs j JOIN users u ON j.recruiter_id = u.id WHERE 1=1"
    params = []

    if search:
        query += " AND (j.title LIKE ? OR j.description LIKE ? OR j.skills_required LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if location:
        query += " AND j.location LIKE ?"
        params.append(f"%{location}%")
    if job_type:
        query += " AND j.job_type = ?"
        params.append(job_type)

    query += " ORDER BY j.created_at DESC"
    jobs = db.execute(query, params).fetchall()

    # Calculate match scores for logged-in candidates
    job_data = []
    for job in jobs:
        job_dict = dict(job)
        if session.get("role") == "candidate":
            resume_skills = get_resume_skills(session["user_id"])
            job_dict["match_score"] = calculate_match_score(resume_skills, job["skills_required"])
        else:
            job_dict["match_score"] = None
        job_data.append(job_dict)

    db.close()
    return render_template("jobs.html", jobs=job_data, search=search, location=location, job_type=job_type)


@app.route("/job/<int:job_id>")
def job_detail(job_id):
    """View a single job posting."""
    db = get_db()
    job = db.execute(
        "SELECT j.*, u.name as recruiter_name FROM jobs j JOIN users u ON j.recruiter_id = u.id WHERE j.id = ?",
        (job_id,),
    ).fetchone()

    if not job:
        flash("Job not found.", "danger")
        db.close()
        return redirect(url_for("job_listings"))

    # Check if already applied
    already_applied = False
    match_score = None
    if session.get("role") == "candidate":
        existing = db.execute(
            "SELECT id FROM applications WHERE user_id = ? AND job_id = ?",
            (session["user_id"], job_id),
        ).fetchone()
        already_applied = existing is not None
        resume_skills = get_resume_skills(session["user_id"])
        match_score = calculate_match_score(resume_skills, job["skills_required"])

    # Get application count for recruiters
    app_count = None
    if session.get("role") == "recruiter":
        app_count = db.execute(
            "SELECT COUNT(*) FROM applications WHERE job_id = ?", (job_id,)
        ).fetchone()[0]

    db.close()
    return render_template(
        "job_detail.html", job=job, already_applied=already_applied,
        match_score=match_score, app_count=app_count
    )


@app.route("/apply/<int:job_id>", methods=["POST"])
@login_required
def apply_job(job_id):
    """Apply to a job (candidate only)."""
    if session.get("role") != "candidate":
        flash("Only candidates can apply to jobs.", "danger")
        return redirect(url_for("job_listings"))

    db = get_db()
    existing = db.execute(
        "SELECT id FROM applications WHERE user_id = ? AND job_id = ?",
        (session["user_id"], job_id),
    ).fetchone()

    if existing:
        flash("You have already applied to this job.", "warning")
        db.close()
        return redirect(url_for("job_detail", job_id=job_id))

    resume_skills = get_resume_skills(session["user_id"])
    if not resume_skills:
        flash("Please upload a resume before applying.", "warning")
        db.close()
        return redirect(url_for("upload_resume"))

    job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    match_score = calculate_match_score(resume_skills, job["skills_required"])

    db.execute(
        "INSERT INTO applications (user_id, job_id, match_score) VALUES (?,?,?)",
        (session["user_id"], job_id, match_score),
    )
    db.commit()
    db.close()
    flash(f"Application submitted! Your match score is {match_score}%.", "success")
    return redirect(url_for("candidate_dashboard"))


# ---------------------------------------------------------------------------
# Candidate Routes
# ---------------------------------------------------------------------------

@app.route("/candidate/dashboard")
@role_required("candidate")
def candidate_dashboard():
    """Candidate dashboard with overview stats."""
    db = get_db()
    user_id = session["user_id"]

    # Resume info
    resume = db.execute("SELECT * FROM resumes WHERE user_id = ?", (user_id,)).fetchone()

    # Applications
    applications = db.execute(
        """SELECT a.*, j.title, j.location, j.salary, j.job_type, u.name as recruiter_name
           FROM applications a
           JOIN jobs j ON a.job_id = j.id
           JOIN users u ON j.recruiter_id = u.id
           WHERE a.user_id = ?
           ORDER BY a.applied_at DESC""",
        (user_id,),
    ).fetchall()

    # Recommended jobs (not yet applied, sorted by match score)
    applied_job_ids = [a["job_id"] for a in applications]
    resume_skills = get_resume_skills(user_id)
    all_jobs = db.execute(
        "SELECT j.*, u.name as recruiter_name FROM jobs j JOIN users u ON j.recruiter_id = u.id"
    ).fetchall()

    recommended = []
    for job in all_jobs:
        if job["id"] not in applied_job_ids:
            score = calculate_match_score(resume_skills, job["skills_required"])
            recommended.append({**dict(job), "match_score": score})
    recommended.sort(key=lambda x: x["match_score"], reverse=True)

    # Profile strength
    strength = calculate_profile_strength(user_id)

    # Stats for chart
    status_counts = {"pending": 0, "shortlisted": 0, "rejected": 0}
    for app in applications:
        status_counts[app["status"]] = status_counts.get(app["status"], 0) + 1

    db.close()
    return render_template(
        "candidate_dashboard.html",
        resume=resume,
        applications=applications,
        recommended=recommended[:6],
        strength=strength,
        status_counts=status_counts,
    )


@app.route("/candidate/upload-resume", methods=["GET", "POST"])
@role_required("candidate")
def upload_resume():
    """Upload and parse resume PDF."""
    if request.method == "POST":
        if "resume" not in request.files:
            flash("No file selected.", "danger")
            return redirect(request.url)

        file = request.files["resume"]
        if file.filename == "":
            flash("No file selected.", "danger")
            return redirect(request.url)

        filename_raw = file.filename or ""
        if not filename_raw.lower().endswith(".pdf"):
            flash("Only PDF files are accepted.", "danger")
            return redirect(request.url)

        filename = secure_filename(f"resume_{session['user_id']}_{file.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Extract text and skills
        text = extract_text_from_pdf(filepath)
        skills = extract_skills_from_text(text)

        # Extract education and experience heuristically
        education = ""
        experience = ""
        lines = text.split("\n")
        edu_lines = []
        exp_lines = []
        in_edu = False
        in_exp = False
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            lower = line_stripped.lower()
            if any(k in lower for k in ["education", "academic", "qualification"]):
                in_edu = True
                in_exp = False
                continue
            if any(k in lower for k in ["experience", "work history", "employment", "professional"]):
                in_exp = True
                in_edu = False
                continue
            if any(k in lower for k in ["skill", "technical", "project", "certification"]):
                in_edu = False
                in_exp = False
                continue
            if in_edu:
                edu_lines.append(line_stripped)
            elif in_exp:
                exp_lines.append(line_stripped)

        education = "\n".join(edu_lines[:5]) if edu_lines else "Not detected"
        experience = "\n".join(exp_lines[:5]) if exp_lines else "Not detected"

        db = get_db()
        existing = db.execute("SELECT id FROM resumes WHERE user_id = ?", (session["user_id"],)).fetchone()
        if existing:
            db.execute(
                "UPDATE resumes SET file_path = ?, extracted_skills = ?, education = ?, experience = ? WHERE user_id = ?",
                (filename, ", ".join(skills), education, experience, session["user_id"]),
            )
        else:
            db.execute(
                "INSERT INTO resumes (user_id, file_path, extracted_skills, education, experience) VALUES (?,?,?,?,?)",
                (session["user_id"], filename, ", ".join(skills), education, experience),
            )
        db.commit()
        db.close()

        flash(f"Resume uploaded! Detected {len(skills)} skills.", "success")
        return redirect(url_for("candidate_dashboard"))

    return render_template("upload_resume.html")


@app.route("/candidate/profile", methods=["GET", "POST"])
@role_required("candidate")
def candidate_profile():
    """Candidate profile page."""
    db = get_db()
    user_id = session["user_id"]

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()
        bio = request.form.get("bio", "").strip()

        db.execute(
            "UPDATE users SET name = ?, phone = ?, location = ?, bio = ? WHERE id = ?",
            (name, phone, location, bio, user_id),
        )
        db.commit()
        session["name"] = name
        flash("Profile updated successfully!", "success")

    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    resume = db.execute("SELECT * FROM resumes WHERE user_id = ?", (user_id,)).fetchone()
    strength = calculate_profile_strength(user_id)
    db.close()
    return render_template("candidate_profile.html", user=user, resume=resume, strength=strength)


@app.route("/candidate/notifications")
@login_required
def notifications():
    """View all notifications for current user."""
    db = get_db()
    notifs = db.execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],),
    ).fetchall()
    # Mark all as read
    db.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (session["user_id"],))
    db.commit()
    db.close()
    return render_template("notifications.html", notifications=notifs)


# ---------------------------------------------------------------------------
# Recruiter Routes
# ---------------------------------------------------------------------------

@app.route("/recruiter/dashboard")
@role_required("recruiter")
def recruiter_dashboard():
    """Recruiter dashboard with overview stats."""
    db = get_db()
    user_id = session["user_id"]

    # Jobs posted by this recruiter
    jobs = db.execute(
        "SELECT * FROM jobs WHERE recruiter_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()

    # Application stats per job
    job_stats = []
    total_apps = 0
    total_shortlisted = 0
    total_pending = 0
    for job in jobs:
        apps = db.execute(
            "SELECT COUNT(*) FROM applications WHERE job_id = ?", (job["id"],)
        ).fetchone()[0]
        shortlisted = db.execute(
            "SELECT COUNT(*) FROM applications WHERE job_id = ? AND status = 'shortlisted'",
            (job["id"],),
        ).fetchone()[0]
        pending = db.execute(
            "SELECT COUNT(*) FROM applications WHERE job_id = ? AND status = 'pending'",
            (job["id"],),
        ).fetchone()[0]
        job_stats.append({**dict(job), "app_count": apps, "shortlisted": shortlisted, "pending": pending})
        total_apps += apps
        total_shortlisted += shortlisted
        total_pending += pending

    # Recent applications
    recent_apps = db.execute(
        """SELECT a.*, j.title as job_title, u.name as candidate_name, u.email as candidate_email
           FROM applications a
           JOIN jobs j ON a.job_id = j.id
           JOIN users u ON a.user_id = u.id
           WHERE j.recruiter_id = ?
           ORDER BY a.applied_at DESC LIMIT 10""",
        (user_id,),
    ).fetchall()

    db.close()
    return render_template(
        "recruiter_dashboard.html",
        job_stats=job_stats,
        recent_apps=recent_apps,
        total_apps=total_apps,
        total_shortlisted=total_shortlisted,
        total_pending=total_pending,
    )


@app.route("/recruiter/post-job", methods=["GET", "POST"])
@role_required("recruiter")
def post_job():
    """Post a new job opening."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        skills = request.form.get("skills_required", "").strip()
        location = request.form.get("location", "").strip()
        salary = request.form.get("salary", "").strip()
        job_type = request.form.get("job_type", "Full-time")

        if not title or not description or not skills:
            flash("Title, description, and skills are required.", "danger")
            return render_template("post_job.html")

        db = get_db()
        db.execute(
            "INSERT INTO jobs (title, description, skills_required, location, salary, job_type, recruiter_id) VALUES (?,?,?,?,?,?,?)",
            (title, description, skills, location, salary, job_type, session["user_id"]),
        )
        db.commit()
        db.close()
        flash("Job posted successfully!", "success")
        return redirect(url_for("recruiter_dashboard"))

    return render_template("post_job.html")


@app.route("/recruiter/job/<int:job_id>/applications")
@role_required("recruiter")
def manage_applications(job_id):
    """View and manage applications for a specific job."""
    db = get_db()
    job = db.execute(
        "SELECT * FROM jobs WHERE id = ? AND recruiter_id = ?",
        (job_id, session["user_id"]),
    ).fetchone()

    if not job:
        flash("Job not found.", "danger")
        db.close()
        return redirect(url_for("recruiter_dashboard"))

    applications = db.execute(
        """SELECT a.*, u.name as candidate_name, u.email as candidate_email,
                  u.phone as candidate_phone, u.location as candidate_location,
                  r.extracted_skills, r.education, r.experience
           FROM applications a
           JOIN users u ON a.user_id = u.id
           LEFT JOIN resumes r ON a.user_id = r.user_id
           WHERE a.job_id = ?
           ORDER BY a.match_score DESC""",
        (job_id,),
    ).fetchall()

    db.close()
    return render_template("manage_applications.html", job=job, applications=applications)


@app.route("/recruiter/application/<int:app_id>/status", methods=["POST"])
@role_required("recruiter")
def update_application_status(app_id):
    """Update application status (shortlist/reject)."""
    status = request.form.get("status")
    if status not in ("pending", "shortlisted", "rejected"):
        flash("Invalid status.", "danger")
        return redirect(request.referrer or url_for("recruiter_dashboard"))

    db = get_db()
    app_row = db.execute(
        """SELECT a.*, j.recruiter_id, j.title, u.name as candidate_name
           FROM applications a
           JOIN jobs j ON a.job_id = j.id
           JOIN users u ON a.user_id = u.id
           WHERE a.id = ?""",
        (app_id,),
    ).fetchone()

    if not app_row or app_row["recruiter_id"] != session["user_id"]:
        flash("Application not found.", "danger")
        db.close()
        return redirect(url_for("recruiter_dashboard"))

    db.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))

    # Create notification for candidate
    status_text = "shortlisted" if status == "shortlisted" else "rejected" if status == "rejected" else "updated"
    message = f"Your application for {app_row['title']} has been {status_text}."
    db.execute(
        "INSERT INTO notifications (user_id, message) VALUES (?,?)",
        (app_row["user_id"], message),
    )
    db.commit()
    db.close()

    flash(f"Application {status}.", "success")
    return redirect(request.referrer or url_for("recruiter_dashboard"))


@app.route("/recruiter/profile", methods=["GET", "POST"])
@role_required("recruiter")
def recruiter_profile():
    """Recruiter profile page."""
    db = get_db()
    user_id = session["user_id"]

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()
        bio = request.form.get("bio", "").strip()

        db.execute(
            "UPDATE users SET name = ?, phone = ?, location = ?, bio = ? WHERE id = ?",
            (name, phone, location, bio, user_id),
        )
        db.commit()
        session["name"] = name
        flash("Profile updated successfully!", "success")

    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    return render_template("recruiter_profile.html", user=user)


# ---------------------------------------------------------------------------
# Chatbot API
# ---------------------------------------------------------------------------

@app.route("/api/chatbot", methods=["POST"])
def chatbot():
    """Simple job-suggestion chatbot."""
    data = request.get_json()
    message = data.get("message", "").lower() if data else ""

    db = get_db()
    resume_skills = ""
    if session.get("role") == "candidate":
        resume_skills = get_resume_skills(session["user_id"])

    # Detect intent
    if any(w in message for w in ["hello", "hi", "hey"]):
        reply = "Hello! I'm MatchAI Assistant. I can help you find jobs that match your skills, or suggest skills to improve your profile. What would you like?"
    elif any(w in message for w in ["suggest", "recommend", "find job", "looking for"]):
        if resume_skills:
            jobs = db.execute("SELECT * FROM jobs").fetchall()
            scored = []
            for job in jobs:
                score = calculate_match_score(resume_skills, job["skills_required"])
                scored.append({"title": job["title"], "score": score, "id": job["id"]})
            scored.sort(key=lambda x: x["score"], reverse=True)
            top = scored[:3]
            lines = [f"  {j['title']} — {j['score']}% match" for j in top]
            reply = "Here are your top job matches:\n" + "\n".join(lines) + "\nVisit the Jobs page to apply!"
        else:
            reply = "I'd recommend uploading your resume first so I can find your best matches! Go to the Resume Upload page."
    elif any(w in message for w in ["skill", "improve", "profile"]):
        if resume_skills:
            skills_list = [s.strip() for s in resume_skills.split(",")][:8]
            reply = f"Your detected skills: {', '.join(skills_list)}.\nTip: Learning cloud (AWS/Docker) or a second language can boost your match scores significantly!"
        else:
            reply = "Upload your resume and I'll analyze your skills and suggest improvements!"
    elif any(w in message for w in ["how many", "count", "stats"]):
        jobs = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        cands = db.execute("SELECT COUNT(*) FROM users WHERE role='candidate'").fetchone()[0]
        reply = f"We currently have {jobs} open positions and {cands} registered candidates. Want me to find jobs for you?"
    else:
        reply = "I can help with job suggestions, skill analysis, or platform stats. Try asking: 'Suggest jobs for me' or 'How can I improve my profile?'"

    db.close()
    return jsonify({"reply": reply})


# ---------------------------------------------------------------------------
# Static file serving for uploads
# ---------------------------------------------------------------------------

@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
