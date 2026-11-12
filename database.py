from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# USER TABLE
class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    phone = db.Column(db.String(20), nullable=True)

    skills = db.Column(db.Text, nullable=True)

    resume_filename = db.Column(db.String(255), nullable=True)

    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    jobs = db.relationship("Job", backref="employer", lazy=True)

    applications = db.relationship(
        "Application",
        backref="applicant",
        lazy=True
    )


# JOB TABLE
class Job(db.Model):

    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)

    employer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(db.String(150), nullable=False)

    company_name = db.Column(db.String(150), nullable=False)

    location = db.Column(db.String(150), nullable=False)

    salary = db.Column(db.String(100))

    job_type = db.Column(db.String(50))

    description = db.Column(db.Text, nullable=False)

    requirements = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship(
        "Application",
        backref="job",
        lazy=True
    )


# APPLICATION TABLE
class Application(db.Model):

    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id"),
        nullable=False
    )

    applicant_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    resume_filename = db.Column(db.String(255))

    status = db.Column(
        db.String(30),
        default="Pending"
    )

    applied_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ADMIN TABLE
class Admin(db.Model):

    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )