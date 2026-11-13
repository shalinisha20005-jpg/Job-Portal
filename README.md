
# Job Portal Web Application

## Project Overview

The Job Portal is a web-based application developed using Python Flask that connects job seekers, employers, and administrators through a single platform.

Job seekers can register, log in, search for jobs, apply for opportunities, upload resumes, and track their application status.

Employers can post job vacancies, view applicants, and manage applications. Administrators can manage users, jobs, and applications through an admin dashboard.

## Project Objectives

- Provide an online platform for job searching and recruitment.
- Simplify the job application process.
- Allow employers to manage job postings and applicants.
- Provide administrators with centralized management.
- Enable users to upload and manage resumes.


## Technologies Used

### Frontend
- HTML5
- CSS3
- JavaScript
- Bootstrap (if used)

### Backend
- Python
- Flask
- Flask-Login
- Flask-SQLAlchemy

### Database
- SQLite (local development)
- PostgreSQL (deployment configuration)

### Development Tools
- Visual Studio Code
- Git
- GitHub
- Render

## Key Features

### Job Seeker Module
- User registration and login.
- Browse available job opportunities.
- Search and filter jobs.
- Apply for jobs.
- Upload and replace PDF resumes.
- Track application status.
- Update personal profile and skills.
- Profile completion progress indicator.

### Employer Module
- Employer registration and login.
- Post new job vacancies.
- Manage job postings.
- View applicant details.
- View applicant resumes.
- Accept or reject applications.

### Admin Module
- Admin login.
- Admin dashboard with statistics.
- Manage users.
- Search and filter users.
- Manage job postings.
- Manage applications.
- Filter applications by status.
## Project Structure

```text
Jobportal/
│
├── app.py
├── database.py
├── requirements.txt
├── Procfile
├── README.md
│
├── instance/
│   └── jobportal.db
│
├── static/
│   ├── css/
│   ├── js/
│   └── resumes/
│
└── templates/
    ├── index.html
    ├── login.html
    ├── register.html
    ├── job_seeker_dashboard.html
    ├── employer_dashboard.html
    ├── admin_dashboard.html
    ├── profile.html
    └── other templates


## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/shalinisha20005-jpg/Job-Portal.git
```

### 2. Open the Project Folder

```bash
cd Job-Portal
```

### 3. Create a Virtual Environment

```bash
python3 -m venv .venv
```

### 4. Activate the Virtual Environment

For macOS/Linux:

```bash
source .venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Set the Secret Key

```bash
export SECRET_KEY="your-generated-secret-key"
```

### 7. Run the Application

```bash
python app.py
```

### 8. Open in Browser

Visit:

http://127.0.0.1:5000

## Application Screenshots

Screenshots of the application will be added here.

- Home Page
- Login and Registration
- Job Seeker Dashboard
- Employer Dashboard
- Admin Dashboard
- Job Listings
- Profile and Resume Management

## Future Enhancements

- Email notifications for job applications.
- Advanced job recommendation system.
- Improved mobile responsiveness.
- Enhanced application tracking.

## Author

**Shalini**

GitHub: https://github.com/shalinisha20005-jpg

## License

This project is developed for educational and academic purposes.
