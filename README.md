# SmartSchool Backend

SmartSchool is a Django REST backend for a school management system focused on the daily workflows of teachers and students. It provides APIs for scores, homework, attendance, teacher comments, user dashboards, JWT authentication, and OpenAPI documentation.

The frontend can live in a separate project. This repository is intended to be the backend/API service.

---

## Highlights

- Role-aware dashboard API for students, teachers, and staff
- JWT authentication with refresh tokens
- RESTful CRUD APIs for core school modules
- OpenAPI schema, Swagger UI, and Redoc documentation
- Teacher-to-student comments with read/unread tracking
- Attendance records with explicit `present` / `absent` status
- Homework management with due-date validation
- Score management with validation and permission checks
- Weekly schedule support for class/lesson planning
- Production-ready deployment with Gunicorn, systemd, and WhiteNoise
- Interactive install/management script with rollback support
- Environment-driven settings through `.env`

---

## Tech Stack

- Python
- Django
- Django REST Framework
- Simple JWT
- drf-spectacular
- SQLite by default
- Gunicorn
- WhiteNoise
- systemd for production service management

---

## Project Structure

```text
.
├── deploy/
│   ├── install.sh                 # Production installer and service manager
│   └── gunicorn/
│       └── gunicorn.conf.py       # Gunicorn production config
├── smartschool/
│   ├── accounts/                  # Current-user dashboard API
│   ├── attendances/               # Attendance and absence records
│   ├── basemodels/                # Grades, subjects, classes, lessons
│   ├── comments/                  # Teacher comments for students
│   ├── homeworks/                 # Homework CRUD
│   ├── scores/                    # Score CRUD
│   ├── students/                  # Student profiles
│   ├── teachers/                  # Teacher profiles and teaching assignments
│   ├── weeklyschedules/           # Weekly class schedules
│   ├── smartschool/               # Django project settings/urls/asgi/wsgi
│   ├── manage.py
│   └── seed_demo_data.py          # Optional demo data seeder
├── .env.sample
├── requirements.txt
└── README.md
```

---

## Core Modules

### Accounts

The `accounts` app exposes the current user's dashboard data. It aggregates the user profile, role, stats, scores, homework, attendance records, comments, teaching assignments, and related students.

Main endpoint:

```text
GET /api/accounts/me/
```

Optional query:

```text
GET /api/accounts/me/?limit=200
```

Use `limit=0` to return all records.

### Scores

Teachers can create, update, list, and delete student scores based on their teaching assignments. Students can read their own scores.

```text
/api/scores/
```

### Homeworks

Teachers can create homework for classes and lessons they teach. Students can see homework for their class.

```text
/api/homeworks/
```

### Attendances

Attendance records are explicit and support two statuses:

```text
present
absent
```

```text
/api/attendances/
```

### Comments

Teachers can send comments/messages to students. Students can see messages and unread/read state is tracked by the `checked` field.

```text
/api/comments/
```

### Weekly Schedules

Weekly schedules define the lessons assigned to each class on each school day and period.

---

## API Documentation

After running the backend, documentation is available at:

```text
/api/schema/   OpenAPI schema
/api/docs/     Swagger UI
/api/redoc/    Redoc UI
```

Example local URLs:

```text
http://127.0.0.1:8000/api/docs/
http://127.0.0.1:8000/api/redoc/
```

---

## Authentication

The project uses JWT authentication.

Get token:

```http
POST /api/token/
Content-Type: application/json

{
  "username": "1",
  "password": "1"
}
```

Refresh token:

```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "your-refresh-token"
}
```

Use access tokens like this:

```http
Authorization: Bearer your-access-token
```

---

## Environment Variables

Copy the sample file:

```bash
cp .env.sample .env
```

Available variables:

```env
SECRET_KEY=change-me
DEBUG=False
ALLOWED_HOSTS=example.com,127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://example.com,http://127.0.0.1:3000,http://localhost:3000
ADMIN_PATH=secure-admin

GUNICORN_BIND=0.0.0.0:8000
GUNICORN_WORKERS=3
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=120
GUNICORN_GRACEFUL_TIMEOUT=30
GUNICORN_KEEPALIVE=5
GUNICORN_LOG_LEVEL=info
```

Notes:

- `.env` is ignored by Git.
- `DEBUG=False` is recommended for production.
- Add your frontend origin to `CORS_ALLOWED_ORIGINS`.
- Add your domain/IP to `ALLOWED_HOSTS`.

---

### Django Admin URL

The Django admin endpoint is configurable through `.env`:

```env
ADMIN_PATH=secure-admin
```

With this value, the admin panel is available at:

```text
/secure-admin/
```

Avoid using the default `/admin/` path in production.
---

## Local Development

### 1. Create virtual environment

```bash
python -m venv env
```

Activate it:

```bash
# Linux/macOS
source env/bin/activate

# Windows PowerShell
.\env\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

```bash
cp .env.sample .env
```

For local development, you can use:

```env
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 4. Run migrations

```bash
cd smartschool
python manage.py migrate
```

### 5. Create admin user

```bash
python manage.py createsuperuser
```

### 6. Run server

```bash
python manage.py runserver
```

Backend will be available at:

```text
http://127.0.0.1:8000/
```

---

## Demo Data

A demo seeder is included:

```bash
cd smartschool
python manage.py shell -c "exec(open('seed_demo_data.py', encoding='utf-8-sig').read())"
```

It creates sample data for:

- Grade 11 mathematics class
- Grade 11 experimental science class
- Teachers
- Students
- Teaching assignments
- Weekly schedules

Generated users use numeric usernames and passwords:

```text
username: 1
password: 1

username: 2
password: 2
```

---

## Production Deployment

This project includes an interactive production installer:

```bash
sudo ./deploy/install.sh
```

Before running it, make sure the script is executable:

```bash
chmod +x deploy/install.sh
```

The installer can:

- Create or reuse a Python virtual environment
- Install dependencies
- Generate `.env`
- Run `manage.py check`
- Run migrations
- Run `collectstatic`
- Create a Gunicorn systemd service
- Start and enable the service
- Roll back on failure or interruption

No Nginx is configured by this installer. Static files are served by WhiteNoise and the app is served directly by Gunicorn.

### Menu Commands

```bash
sudo ./deploy/install.sh
```

Or run actions directly:

```bash
sudo ./deploy/install.sh install
sudo ./deploy/install.sh status
sudo ./deploy/install.sh restart
sudo ./deploy/install.sh logs
sudo ./deploy/install.sh uninstall
sudo ./deploy/install.sh rollback
```

### Rollback Behavior

The installer tracks files and directories created during installation and keeps backups of replaced files.

If installation fails or is interrupted with `Ctrl+C`, it attempts to roll back automatically.

If the SSH session or server process is interrupted, run:

```bash
sudo ./deploy/install.sh rollback
```

---

## systemd Service

The installer creates a service similar to:

```text
/etc/systemd/system/smartschool.service
```

Common commands:

```bash
sudo systemctl status smartschool
sudo systemctl restart smartschool
sudo journalctl -u smartschool -f
```

---

## Gunicorn

Gunicorn configuration lives here:

```text
deploy/gunicorn/gunicorn.conf.py
```

It reads runtime values from `.env`:

```env
GUNICORN_BIND=0.0.0.0:8000
GUNICORN_WORKERS=3
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=120
```

---

## Static Files

Static files are collected into:

```text
smartschool/staticfiles/
```

This directory should not be committed. It can always be regenerated:

```bash
cd smartschool
python manage.py collectstatic --noinput
```

WhiteNoise is already enabled in `settings.py`.

---

## Frontend Integration

The frontend is expected to be a separate project.

Configure the frontend API base URL to point to this backend, for example:

```text
http://127.0.0.1:8000
https://api.example.com
```

Also add the frontend origin to `.env`:

```env
CORS_ALLOWED_ORIGINS=https://school.example.com,http://localhost:3000
```

---

## Useful API Endpoints

```text
POST /api/token/
POST /api/token/refresh/
GET  /api/accounts/me/
GET  /api/schema/
GET  /api/docs/
GET  /api/redoc/

/api/scores/
/api/homeworks/
/api/attendances/
/api/comments/
```

---

## Development Checks

Run Django checks:

```bash
cd smartschool
python manage.py check
```

Check for missing migrations:

```bash
python manage.py makemigrations --check --dry-run
```

Run migrations:

```bash
python manage.py migrate
```

---

## Git Notes

The repository should not include runtime/generated files such as:

```text
.env
env/
smartschool/db.sqlite3
smartschool/staticfiles/
.deploy_rollback/
```

Commit source files, migrations, deployment templates, and documentation.

---

## License

Add your preferred license here before publishing publicly.

