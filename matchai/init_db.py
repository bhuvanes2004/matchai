"""Database initialization script with sample data."""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = "database.db"


def init_database():
    """Create tables and populate with sample data."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Create Tables ---
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('candidate', 'recruiter')),
            phone TEXT DEFAULT '',
            location TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            skills_required TEXT NOT NULL,
            location TEXT DEFAULT '',
            salary TEXT DEFAULT '',
            job_type TEXT DEFAULT 'Full-time',
            recruiter_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recruiter_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            extracted_skills TEXT DEFAULT '',
            education TEXT DEFAULT '',
            experience TEXT DEFAULT '',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            match_score REAL DEFAULT 0,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'shortlisted', 'rejected')),
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    # --- Sample Data ---
    # Recruiter passwords
    pw_recruiter1 = generate_password_hash("recruiter123")
    pw_recruiter2 = generate_password_hash("recruiter123")
    # Candidate passwords
    pw_candidate1 = generate_password_hash("candidate123")
    pw_candidate2 = generate_password_hash("candidate123")
    pw_candidate3 = generate_password_hash("candidate123")

    # Users
    cursor.executemany(
        "INSERT INTO users (name, email, password, role, phone, location, bio) VALUES (?,?,?,?,?,?,?)",
        [
            ("Sarah Johnson", "recruiter@matchai.com", pw_recruiter1, "recruiter",
             "+1-555-0101", "San Francisco, CA", "Senior Talent Acquisition Lead at TechCorp with 8 years of experience."),
            ("Mike Chen", "mike@matchai.com", pw_recruiter2, "recruiter",
             "+1-555-0102", "New York, NY", "HR Manager at DataDriven Inc specializing in data science recruitment."),
            ("Alice Williams", "alice@matchai.com", pw_candidate1, "candidate",
             "+1-555-0201", "Austin, TX", "Full-stack developer with 5 years of experience in Python and JavaScript."),
            ("Bob Martinez", "bob@matchai.com", pw_candidate2, "candidate",
             "+1-555-0202", "Seattle, WA", "Data scientist passionate about machine learning and AI."),
            ("Carol Davis", "carol@matchai.com", pw_candidate3, "candidate",
             "+1-555-0203", "Chicago, IL", "UX designer with a strong background in user research and prototyping."),
        ],
    )

    # Jobs
    cursor.executemany(
        "INSERT INTO jobs (title, description, skills_required, location, salary, job_type, recruiter_id) VALUES (?,?,?,?,?,?,?)",
        [
            ("Senior Python Developer",
             "We are looking for a Senior Python Developer to join our backend team. You will design and implement scalable microservices, work with cloud infrastructure, and mentor junior developers.",
             "Python, Django, Flask, PostgreSQL, Docker, AWS, REST API, Git",
             "San Francisco, CA", "$130,000 - $170,000", "Full-time", 1),
            ("Data Scientist",
             "Join our analytics team to build predictive models and derive insights from large datasets. You will collaborate with product and engineering teams to drive data-informed decisions.",
             "Python, Machine Learning, TensorFlow, Pandas, SQL, Statistics, Data Visualization, Scikit-learn",
             "New York, NY", "$120,000 - $160,000", "Full-time", 2),
            ("Frontend React Developer",
             "Build beautiful, responsive user interfaces using React. You will work closely with designers to implement pixel-perfect UIs and ensure great performance.",
             "JavaScript, React, TypeScript, HTML, CSS, Redux, Bootstrap, Git",
             "Remote", "$100,000 - $140,000", "Full-time", 1),
            ("DevOps Engineer",
             "Manage and improve our CI/CD pipelines, cloud infrastructure, and monitoring systems. You will ensure high availability and reliability of our production systems.",
             "Docker, Kubernetes, AWS, Jenkins, Linux, Terraform, Python, CI/CD",
             "San Francisco, CA", "$140,000 - $180,000", "Full-time", 1),
            ("Machine Learning Engineer",
             "Design and deploy machine learning models at scale. You will work on recommendation systems, NLP pipelines, and computer vision applications.",
             "Python, PyTorch, Machine Learning, Deep Learning, NLP, Computer Vision, Docker, AWS",
             "New York, NY", "$140,000 - $190,000", "Full-time", 2),
            ("Full Stack Developer",
             "Work on both frontend and backend of our SaaS platform. You will own features end-to-end from database to UI.",
             "Python, JavaScript, React, Node.js, PostgreSQL, MongoDB, Docker, REST API",
             "Austin, TX", "$110,000 - $150,000", "Full-time", 1),
            ("UX/UI Designer",
             "Create intuitive and visually appealing user experiences. Conduct user research, create wireframes, prototypes, and work with developers to bring designs to life.",
             "Figma, Adobe XD, User Research, Wireframing, Prototyping, CSS, HTML, Usability Testing",
             "Chicago, IL", "$90,000 - $130,000", "Full-time", 2),
            ("Junior Data Analyst",
             "Analyze business data to identify trends and provide actionable insights. Create dashboards and reports for stakeholders.",
             "SQL, Python, Excel, Tableau, Power BI, Statistics, Data Visualization",
             "Remote", "$65,000 - $85,000", "Full-time", 2),
        ],
    )

    # Resumes for candidates
    cursor.executemany(
        "INSERT INTO resumes (user_id, file_path, extracted_skills, education, experience) VALUES (?,?,?,?,?)",
        [
            (3, "uploads/sample_alice.pdf",
             "Python, JavaScript, React, Django, Flask, PostgreSQL, Docker, AWS, REST API, Git, Node.js, HTML, CSS",
             "B.S. Computer Science, University of Texas at Austin, 2018",
             "5 years: Full-Stack Developer at StartupXYZ (2020-Present), Junior Developer at WebCo (2018-2020)"),
            (4, "uploads/sample_bob.pdf",
             "Python, Machine Learning, TensorFlow, Pandas, SQL, Statistics, Scikit-learn, Data Visualization, Deep Learning, NLP, PyTorch",
             "M.S. Data Science, University of Washington, 2020",
             "3 years: Data Scientist at AnalyticsPro (2021-Present), Data Analyst at InsightCo (2020-2021)"),
            (5, "uploads/sample_carol.pdf",
             "Figma, Adobe XD, User Research, Wireframing, Prototyping, CSS, HTML, Usability Testing, JavaScript, React",
             "B.A. Graphic Design, School of the Art Institute of Chicago, 2019",
             "4 years: Senior UX Designer at DesignHub (2022-Present), UX Designer at CreativeApps (2019-2022)"),
        ],
    )

    # Applications
    cursor.executemany(
        "INSERT INTO applications (user_id, job_id, match_score, status) VALUES (?,?,?,?)",
        [
            (3, 1, 87.5, "shortlisted"),
            (3, 3, 62.5, "pending"),
            (3, 6, 87.5, "pending"),
            (4, 2, 87.5, "shortlisted"),
            (4, 5, 87.5, "pending"),
            (4, 8, 50.0, "rejected"),
            (5, 7, 88.9, "shortlisted"),
            (5, 3, 25.0, "pending"),
        ],
    )

    # Notifications
    cursor.executemany(
        "INSERT INTO notifications (user_id, message, is_read) VALUES (?,?,?)",
        [
            (3, "Your application for Senior Python Developer has been shortlisted!", 0),
            (3, "New job posted: Full Stack Developer in Austin, TX", 1),
            (4, "Your application for Data Scientist has been shortlisted!", 0),
            (4, "Your application for Junior Data Analyst was not selected.", 1),
            (5, "Your application for UX/UI Designer has been shortlisted!", 0),
        ],
    )

    conn.commit()
    conn.close()
    print("Database initialized with sample data.")


if __name__ == "__main__":
    init_database()
