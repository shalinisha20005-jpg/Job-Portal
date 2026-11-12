import email

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from uuid import uuid4
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from database import db, User, Job, Application
from sqlalchemy import or_
from flask import current_app
import re

app = Flask(__name__)
# Email configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = "jobportal.team123@gmail.com"
app.config["MAIL_PASSWORD"] = "shalushaju29"
app.config["MAIL_DEFAULT_SENDER"] = "jobportal.team123@gmail.com"
app.config["MAIL_DEBUG"] = True
app.config["MAIL_SUPPRESS_SEND"] = False
mail = Mail(app)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY environment variable is not set")
database_url = os.environ.get("DATABASE_URL")

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://", "postgresql+psycopg://", 1
        )
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://", "postgresql+psycopg://", 1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jobportal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path, "static", "resumes"
)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() == "pdf"
    )


db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()

    from sqlalchemy import text

    with db.engine.connect() as connection:
        columns = [
            column["name"]
            for column in db.inspect(db.engine).get_columns("users")
        ]

        if "phone" not in columns:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
            )

        if "skills" not in columns:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN skills TEXT")
            )
        if "resume_filename" not in columns:
            connection.execute(
               text("ALTER TABLE users ADD COLUMN resume_filename VARCHAR(255)")
            )

        connection.commit()


@app.route("/")
def home():
    return render_template("index.html")


# REGISTER

@app.route("/register", methods=["GET", "POST"])
def register():

    # Only display the registration page when opening it
    if request.method == "GET":
        return render_template("register.html")

    # Get details submitted by the user
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    role = request.form.get("role", "")

    # Validate fields
    if not full_name or not email or not password or not role:
        flash("Please fill in all required details.", "error")
        return redirect(url_for("register"))

    if role not in ["job_seeker", "employer"]:
        flash("Please select a valid account type.", "error")
        return redirect(url_for("register"))

    if len(password) < 8:
        flash("Password must contain at least 8 characters.", "error")
        return redirect(url_for("register"))

    # Check duplicate email
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        flash("Email already registered. Please log in.", "error")
        return redirect(url_for("login"))

    # Save user
    user = User(
        full_name=full_name,
        email=email,
        password=generate_password_hash(password),
        role=role
    )

    db.session.add(user)
    db.session.commit()

    flash("Registration successful! Please log in.", "success")
    return redirect(url_for("login"))

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    db.session.commit()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")

# ADMIN LOGIN
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        from database import Admin

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):
           session["admin_id"] = admin.id

           flash("Admin login successful!", "success")

           return redirect(url_for("admin_dashboard"))

        else:
           flash("Invalid username or password!", "error")
    return render_template("admin_login.html")



# ROLE-BASED DASHBOARD ROUTER
@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "employer":
        return redirect(url_for("employer_dashboard"))

    return redirect(url_for("job_seeker_dashboard"))


# JOB SEEKER DASHBOARD
@app.route("/job-seeker/dashboard")
@login_required
def job_seeker_dashboard():
    if current_user.role != "job_seeker":
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))

    total_jobs = Job.query.count()

    total_applications = Application.query.filter_by(
       applicant_id=current_user.id
    ).count()
    recent_applications = Application.query.filter_by(
    applicant_id=current_user.id
    ).order_by(
    Application.id.desc()
    ).limit(5).all()

    pending_applications = Application.query.filter_by(
       applicant_id=current_user.id,
       status="Pending"
    ).count()

    accepted_applications = Application.query.filter_by(
       applicant_id=current_user.id,
       status="Accepted"
    ).count()

    rejected_applications = Application.query.filter_by(
      applicant_id=current_user.id,
      status="Rejected"
    ).count()

    profile_fields = [
    current_user.full_name,
    current_user.email
   ]

    completed_fields = sum(
      1 for field in profile_fields if field
    )

    profile_completion = int(
       (completed_fields / len(profile_fields)) * 100
    )  

    return render_template(
        "job_seeker_dashboard.html",
        total_jobs=total_jobs,
        total_applications=total_applications,
        recent_applications=recent_applications,
        profile_completion=profile_completion,
        pending_applications=pending_applications,
        accepted_applications=accepted_applications,
        rejected_applications=rejected_applications
    )


# EMPLOYER DASHBOARD
@app.route("/employer/dashboard")
@login_required
def employer_dashboard():
    if current_user.role != "employer":
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))

    employer_jobs = Job.query.filter_by(
        employer_id=current_user.id
    ).all()

    return render_template(
        "employer_dashboard.html",
        employer_jobs=employer_jobs
    )

# VIEW APPLICANTS
@app.route("/employer/applicants")
@login_required
def employer_applicants():

    if current_user.role != "employer":
        flash("Access denied. Employers only.", "error")
        return redirect(url_for("dashboard"))

    applications = (
        Application.query
        .join(Job, Application.job_id == Job.id)
        .filter(Job.employer_id == current_user.id)
        .order_by(Application.applied_at.desc())
        .all()
    )

    return render_template(
        "applicants.html",
        applications=applications
    )

# ADMIN DASHBOARD
@app.route("/admin/dashboard")
def admin_dashboard():

    from database import Admin

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    total_users = User.query.count()
    total_jobs = Job.query.count()
    total_applications = Application.query.count()
    pending_applications = Application.query.filter_by(
      status="Pending"
      ).count()

    accepted_applications = Application.query.filter_by(
      status="Accepted"
      ).count()

    rejected_applications = Application.query.filter_by(
      status="Rejected"
      ).count()

    total_employers = User.query.filter_by(role="employer").count()
    total_job_seekers = User.query.filter_by(role="job_seeker").count()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_jobs=total_jobs,
        total_applications=total_applications,
        pending_applications=pending_applications,
        accepted_applications=accepted_applications,
        rejected_applications=rejected_applications,
        total_employers=total_employers,
        total_job_seekers=total_job_seekers
    )


@app.route("/admin/users")
def admin_users():
    if "admin_id" not in session:
        flash("Please login as admin first.", "error")
        return redirect(url_for("admin_login"))

    search = request.args.get("search", "").strip()
    role = request.args.get("role", "").strip()

    query = User.query

    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.role.ilike(f"%{search}%")
            )
        )

    if role in ["job_seeker", "employer"]:
        query = query.filter_by(role=role)

    users = query.order_by(User.created_at.desc()).all()

    return render_template(
        "admin_users.html",
        users=users,
        search=search,
        role=role
    )


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
def admin_delete_user(user_id):
    if "admin_id" not in session:
        flash("Please login as admin first.", "error")
        return redirect(url_for("admin_login"))

    user = db.session.get(User, user_id)

    if user is None:
        flash("User not found.", "error")
        return redirect(url_for("admin_users"))

    try:
        # Delete applications submitted by this user
        Application.query.filter_by(applicant_id=user.id).delete()

        # Delete applications for jobs posted by this user
        user_jobs = Job.query.filter_by(employer_id=user.id).all()

        for job in user_jobs:
            Application.query.filter_by(job_id=job.id).delete()
            db.session.delete(job)

        # Delete the user
        db.session.delete(user)
        db.session.commit()

        flash("User and related records deleted successfully.", "success")

    except Exception:
        db.session.rollback()
        flash("Unable to delete user. Please try again.", "error")

    return redirect(url_for("admin_users"))


@app.route("/admin/jobs")
def admin_jobs():
    if "admin_id" not in session:
        flash("Please login as admin first.", "error")
        return redirect(url_for("admin_login"))

    search = request.args.get("search", "").strip()

    query = Job.query

    if search:
        query = query.filter(
            db.or_(
                Job.title.ilike(f"%{search}%"),
                Job.company_name.ilike(f"%{search}%"),
                Job.location.ilike(f"%{search}%")
            )
        )

    jobs = query.order_by(Job.created_at.desc()).all()

    return render_template(
        "admin_jobs.html",
        jobs=jobs,
        search=search
    )

@app.route("/admin/job/<int:job_id>/delete", methods=["POST"])
def admin_delete_job(job_id):
    if "admin_id" not in session:
        flash("Please login as admin first.", "error")
        return redirect(url_for("admin_login"))

    job = db.session.get(Job, job_id)

    if job is None:
        flash("Job not found.", "error")
        return redirect(url_for("admin_jobs"))

    try:
        # Delete applications connected to this job first
        Application.query.filter_by(job_id=job.id).delete()

        # Delete the job
        db.session.delete(job)
        db.session.commit()

        flash("Job and its applications deleted successfully.", "success")

    except Exception:
        db.session.rollback()
        flash("Unable to delete job. Please try again.", "error")

    return redirect(url_for("admin_jobs"))

@app.route("/admin/applications")
def admin_applications():
    if "admin_id" not in session:
        flash("Please login as admin first.", "error")
        return redirect(url_for("admin_login"))

    status = request.args.get("status", "").strip()

    query = Application.query

    if status in ["Pending", "Accepted", "Rejected"]:
        query = query.filter_by(status=status)

    applications = query.order_by(
        Application.applied_at.desc()
    ).all()

    return render_template(
        "admin_applications.html",
        applications=applications,
        status=status
    )

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    flash("Admin logged out successfully.", "success")
    return redirect(url_for("admin_login"))

# UPDATE APPLICATION STATUS

@app.route("/employer/application/<int:application_id>/update",
           methods=["POST"])
@login_required
def update_application(application_id):

    if current_user.role != "employer":
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))

    application = db.session.get(Application, application_id)

    if application is None:
        flash("Application not found.", "error")
        return redirect(url_for("employer_applicants"))

    # Ensure this employer owns the job
    if application.job.employer_id != current_user.id:
        flash("You cannot update this application.", "error")
        return redirect(url_for("employer_applicants"))

    new_status = request.form.get("status", "")

    if new_status not in ["Pending", "Accepted", "Rejected"]:
        flash("Invalid application status.", "error")
        return redirect(url_for("employer_applicants"))

    application.status = new_status
    db.session.commit()

    # Send email notification
    if new_status in ["Accepted", "Rejected"]:
        try:
            applicant_email = application.applicant.email

            if new_status == "Accepted":
                subject = "Congratulations! Your Job Application is Accepted"
                body = f"""
Hello {application.applicant.full_name},

Congratulations! Your application for
{application.job.title} at {application.job.company_name}
has been accepted.

Best wishes,
JobPortal Team
"""
            else:
                subject = "Your Job Application Status"
                body = f"""
Hello {application.applicant.full_name},

Your application for
{application.job.title} at {application.job.company_name}
has been rejected.

Don't give up! Keep applying for other opportunities.

Best wishes,
JobPortal Team
"""

            msg = Message(
                subject=subject,
                recipients=[applicant_email],
                body=body
            )

            mail.send(msg)

            print("Email notification sent successfully!")

        except Exception as e:
            print("Email notification failed:", e)

    flash("Application status updated successfully!", "success")

    return redirect(url_for("employer_applicants"))

# POST A JOB
@app.route("/post-job", methods=["GET", "POST"])
@login_required
def post_job():

    if current_user.role != "employer":
        flash("Only employers can post jobs.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        company_name = request.form.get("company_name", "").strip()
        location = request.form.get("location", "").strip()
        salary = request.form.get("salary", "").strip()
        job_type = request.form.get("job_type", "").strip()
        description = request.form.get("description", "").strip()
        requirements = request.form.get("requirements", "").strip()

        if not title or not company_name or not location or not job_type or not description:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("post_job"))

        new_job = Job(
            employer_id=current_user.id,
            title=title,
            company_name=company_name,
            location=location,
            salary=salary,
            job_type=job_type,
            description=description,
            requirements=requirements
        )

        db.session.add(new_job)
        db.session.commit()

        flash("Job published successfully!", "success")
        return redirect(url_for("employer_dashboard"))

    return render_template("post_job.html")



# JOB LIST


@app.route("/jobs")
@login_required
def jobs():

    keyword = request.args.get("keyword", "").strip()
    location = request.args.get("location", "").strip()
    job_type = request.args.get("job_type", "").strip()

    query = Job.query

    if keyword:
        query = query.filter(
            Job.title.ilike(f"%{keyword}%") |
            Job.company_name.ilike(f"%{keyword}%")
        )

    if location:
        query = query.filter(
            Job.location.ilike(f"%{location}%")
        )

    if job_type:
        query = query.filter(
            Job.job_type.ilike(f"%{job_type}%")
        )

    sort_by = request.args.get("sort_by", "newest")

    if sort_by == "oldest":
      query = query.order_by(Job.created_at.asc())
    else:
      query = query.order_by(Job.created_at.desc())

    all_jobs = query.all()
    return render_template(
        "jobs.html",
        jobs=all_jobs
    )

@app.route("/job-details/<int:job_id>")
@login_required
def job_details(job_id):
    job = db.session.get(Job, job_id)

    if job is None:
        flash("Job not found.", "error")
        return redirect(url_for("jobs"))

    return render_template("job_details.html", job=job)

# APPLY FOR A JOB
@app.route("/apply/<int:job_id>", methods=["POST"])
@login_required
def apply_job(job_id):

    if current_user.role != "job_seeker":
        flash("Only job seekers can apply for jobs.", "error")
        return redirect(url_for("jobs"))

    job = db.session.get(Job, job_id)

    if job is None:
        flash("Job not found.", "error")
        return redirect(url_for("jobs"))

    # Prevent duplicate applications
    existing_application = Application.query.filter_by(
        job_id=job_id,
        applicant_id=current_user.id
    ).first()

    if existing_application:
        flash("You have already applied for this job.", "error")
        return redirect(url_for("job_details", job_id=job_id))

    # Get uploaded resume
    resume = request.files.get("resume")

    if not resume or resume.filename == "":
        flash("Please upload your resume.", "error")
        return redirect(url_for("job_details", job_id=job_id))

    if not allowed_file(resume.filename):
        flash("Only PDF resumes are allowed.", "error")
        return redirect(url_for("job_details", job_id=job_id))

    # Validate PDF file signature
    if resume.stream.read(5) != b"%PDF-":
        flash("Please upload a valid PDF file.", "error")
        return redirect(url_for("job_details", job_id=job_id))

    resume.stream.seek(0)

    # Create unique filename
    original_name = secure_filename(resume.filename)
    filename = f"{uuid4().hex}_{original_name}"

    resume_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    resume.save(resume_path)

    # Save application to database
    application = Application(
        job_id=job_id,
        applicant_id=current_user.id,
        resume_filename=filename,
        status="Pending"
    )

    try:
        db.session.add(application)
        db.session.commit()

    except Exception:
        db.session.rollback()

        if os.path.exists(resume_path):
            os.remove(resume_path)

        flash("Application failed. Please try again.", "error")
        return redirect(url_for("job_details", job_id=job_id))

    flash("Your application has been submitted successfully!", "success")

    return redirect(url_for("my_applications"))



# MY APPLICATIONS
@app.route("/my-applications")
@login_required
def my_applications():
    applications = Application.query.filter_by(
        applicant_id=current_user.id
    ).all()

    return render_template(
        "my_applications.html",
        applications=applications
    )


# PROFILE



@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        skills = request.form.get("skills", "").strip()

        # Validate required fields
        if not full_name or not email:
          flash("Full name and email are required.", "error")
          return redirect(url_for("profile"))

       # Validate email
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        if not re.match(email_pattern, email):
          flash("Please enter a valid email address.", "error")
          return redirect(url_for("profile"))

        # Validate phone number (10 digits if provided)
        if phone and not re.fullmatch(r"[0-9]{10}", phone):
           flash("Phone number must contain exactly 10 digits.", "error")
           return redirect(url_for("profile"))

        # Check duplicate email
        existing_user = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()

        if existing_user:
            flash("This email is already registered.", "error")
            return redirect(url_for("profile"))

        # Update profile information
        current_user.full_name = full_name
        current_user.email = email
        current_user.phone = phone
        current_user.skills = skills

        
# Resume upload (only when a new file is selected)
        resume_file = request.files.get("resume")

        if resume_file and resume_file.filename:
            if not resume_file.filename.lower().endswith(".pdf"):
                flash("Only PDF resumes are allowed.", "error")
                return redirect(url_for("profile"))

            os.makedirs("static/resumes", exist_ok=True)

            filename = secure_filename(resume_file.filename)
            saved_filename = f"user_{current_user.id}_{filename}"
            resume_path = os.path.join("static", "resumes", saved_filename)

            resume_file.save(resume_path)

            old_resume = current_user.resume_filename
            if old_resume and old_resume != saved_filename:
                old_resume_path = os.path.join("static", "resumes", old_resume)
                if os.path.exists(old_resume_path):
                    os.remove(old_resume_path)

            current_user.resume_filename = saved_filename

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    # Profile completion
    profile_fields = [
        current_user.full_name,
        current_user.email,
        current_user.phone,
        current_user.skills
    ]

    completed_fields = sum(1 for field in profile_fields if field)
    total_fields = len(profile_fields)
    profile_completion = int((completed_fields / total_fields) * 100)

    return render_template("profile.html", profile_completion=profile_completion)



# LOGOUT
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
