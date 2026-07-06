<div align="center">

# 🎓 SmartSchool Backend

**A Django REST backend for school management — scores, homework, attendance, comments, schedules, and role-aware dashboards.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.16-A30000?logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

[Features](#-features) • [Quick Start](#-quick-start-production) • [Local Development](#-local-development) • [API Docs](#-api-documentation) • [Installer](#-installer--manager) • [Frontend](https://github.com/EXE88/smartschool-UI)

</div>

---

## 📌 Overview

SmartSchool is the backend/API service of a school management system focused on the daily workflows of **teachers** and **students**. It ships with JWT authentication, OpenAPI documentation, and a one-command production installer with rollback support.

The official frontend lives in a separate repository: **[EXE88/smartschool-UI](https://github.com/EXE88/smartschool-UI)**.

## ✨ Features

- 👤 **Role-aware dashboard API** — one endpoint returns everything the current user needs
- 🔐 **JWT authentication** with refresh tokens (Simple JWT)
- 🏆 **Scores** — teachers manage scores for their own teaching assignments
- 📚 **Homework** — creation with due-date validation, scoped to the teacher's classes
- 🗓️ **Attendance** — explicit `present` / `absent` records
- 💬 **Comments** — teacher-to-student messages with read/unread tracking
- 📅 **Weekly schedules** — per-class, per-day lesson planning
- 📖 **OpenAPI schema** with Swagger UI and Redoc
- 🛡️ **Configurable admin path** — hide `/admin/` behind a custom URL
- 🚀 **Production-ready** — Gunicorn + WhiteNoise + systemd, no Nginx required
- 🧰 **Interactive installer** — colorful menu, guided `.env` setup, automatic rollback, demo data seeding

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| Framework | Django 6 + Django REST Framework |
| Auth | Simple JWT |
| API docs | drf-spectacular (Swagger / Redoc) |
| Database | SQLite (default) |
| App server | Gunicorn |
| Static files | WhiteNoise |
| Process manager | systemd |

## 🗂️ Project Structure

```text
.
├── install.sh                     # Interactive installer & manager (Linux)
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
│   ├── smartschool/               # Django settings / urls / wsgi / asgi
│   ├── gunicorn.conf.py           # Gunicorn production config
│   ├── seed_demo_data.py          # Optional demo data seeder
│   └── manage.py
├── .env.sample
├── requirements.txt
└── README.md
```

## 🚀 Quick Start (Production)

On a Linux server with systemd:

```bash
git clone https://github.com/EXE88/smartschool.git
cd smartschool
chmod +x install.sh
sudo ./install.sh
```

Pick **Full installation** from the menu (or run `sudo ./install.sh install` directly). The installer walks you through everything:

1. Optional **proxy** setup for restricted networks
2. **Virtual environment** creation and dependency installation
3. Guided **`.env` configuration** (auto-generated `SECRET_KEY`, hosts, CORS, admin path, Gunicorn tuning)
4. Django checks, **migrations**, and **collectstatic**
5. Optional **superuser** creation and **demo data** seeding
6. A **systemd service** that starts on boot and auto-restarts on failure

When it finishes, the API is live at your configured bind address (default `0.0.0.0:8000`).

> 💡 If anything fails — or you press `Ctrl+C` mid-install — the installer **rolls back automatically**, so you can re-run it cleanly.

## 🧭 Installer & Manager

`install.sh` is not just an installer — re-run it anytime to manage individual parts without reinstalling:

```bash
sudo ./install.sh              # interactive menu
```

| Command | What it does |
|---|---|
| `install` | Full installation |
| `env` | Reconfigure `.env` interactively |
| `gunicorn` | Tune Gunicorn (bind, workers, timeouts) |
| `deps` | (Re)install Python dependencies |
| `migrate` | Run database migrations |
| `collectstatic` | Collect static files |
| `superuser` | Create a Django superuser |
| `demo-seed` / `demo-remove` | Add or cleanly remove demo data |
| `status` / `start` / `stop` / `restart` / `logs` | Manage the systemd service |
| `service` | (Re)create the systemd unit file |
| `proxy` | Configure a download proxy |
| `rollback` | Roll back a failed/interrupted installation |
| `uninstall` | Remove the service and optionally venv / `.env` / static / db |

Example:

```bash
sudo ./install.sh restart
sudo ./install.sh logs
sudo ./install.sh demo-seed
```

### ♻️ Rollback

Every file, directory, and service the installer creates is recorded in a manifest (`.installer/`). Replaced files (like an existing `.env` or database) are backed up first. On failure or `Ctrl+C`, changes are reverted automatically — or manually with:

```bash
sudo ./install.sh rollback
```

### 🌐 Proxy Support

On restricted networks, the installer can route downloads through a proxy:

```text
http://127.0.0.1:8080
socks5://127.0.0.1:1080
http://user:pass@proxy.example.com:8080
```

The proxy is exported as `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` and passed to `pip --proxy`. It is remembered for later runs and can be changed via `sudo ./install.sh proxy`.

## ⚙️ Environment Variables

The installer generates `.env` for you, but you can also copy the sample manually:

```bash
cp .env.sample .env
```

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | Django secret key (auto-generated by the installer) |
| `DEBUG` | `False` | Never enable in production |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated domains/IPs |
| `CORS_ALLOWED_ORIGINS` | localhost origins | Add your frontend origin |
| `ADMIN_PATH` | `secure-admin` | Django admin URL path (avoid `admin`) |
| `GUNICORN_BIND` | `0.0.0.0:8000` | Bind address |
| `GUNICORN_WORKERS` | `3` | Worker processes |
| `GUNICORN_THREADS` | `2` | Threads per worker |
| `GUNICORN_TIMEOUT` | `120` | Request timeout (seconds) |
| `GUNICORN_GRACEFUL_TIMEOUT` | `30` | Graceful shutdown timeout |
| `GUNICORN_KEEPALIVE` | `5` | Keep-alive seconds |
| `GUNICORN_LOG_LEVEL` | `info` | Gunicorn log level |

> `.env` is git-ignored. With `ADMIN_PATH=secure-admin`, the admin panel is served at `/secure-admin/`.

## 🧪 Local Development

```bash
# 1. Virtual environment
python -m venv env
source env/bin/activate          # Linux/macOS
.\env\Scripts\Activate.ps1       # Windows PowerShell

# 2. Dependencies
pip install -r requirements.txt

# 3. Environment
cp .env.sample .env              # set DEBUG=True for development

# 4. Database & admin user
cd smartschool
python manage.py migrate
python manage.py createsuperuser

# 5. Run
python manage.py runserver
```

The backend is now available at `http://127.0.0.1:8000/`.

## 🌱 Demo Data

Seed sample data (two grade-11 classes with teachers, students, teaching assignments, and weekly schedules):

```bash
# via the installer
sudo ./install.sh demo-seed

# or manually
cd smartschool
python manage.py shell -c "exec(open('seed_demo_data.py', encoding='utf-8-sig').read())"
```

Generated users have numeric usernames with matching passwords:

```text
username: 1   password: 1
username: 2   password: 2
```

Remove all demo data cleanly (demo users are tagged internally, so real data is untouched):

```bash
sudo ./install.sh demo-remove
```

## 🔐 Authentication

The API uses JWT (Bearer) authentication.

```http
POST /api/token/
Content-Type: application/json

{ "username": "1", "password": "1" }
```

```http
POST /api/token/refresh/
Content-Type: application/json

{ "refresh": "your-refresh-token" }
```

Then send requests with:

```http
Authorization: Bearer your-access-token
```

## 📖 API Documentation

Once the server is running:

| URL | Description |
|---|---|
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | Redoc |
| `/api/schema/` | Raw OpenAPI schema |

### Main Endpoints

```text
POST /api/token/            obtain JWT
POST /api/token/refresh/    refresh JWT
GET  /api/accounts/me/      current-user dashboard (?limit=200, limit=0 for all)

/api/scores/                score CRUD
/api/homeworks/             homework CRUD
/api/attendances/           attendance records
/api/comments/              teacher → student comments
```

## 🛠️ systemd Service

The installer creates `/etc/systemd/system/smartschool.service` with `Restart=always`, so the app survives crashes and server reboots. Manage it via the installer or directly:

```bash
sudo systemctl status smartschool
sudo systemctl restart smartschool
sudo journalctl -u smartschool -f
```

Gunicorn configuration lives in [smartschool/gunicorn.conf.py](smartschool/gunicorn.conf.py) and reads its runtime values from `.env`. Static files are served by WhiteNoise directly from Gunicorn — no Nginx required.

## 🔌 Frontend Integration

The official frontend: **[EXE88/smartschool-UI](https://github.com/EXE88/smartschool-UI)**

1. Point the frontend's API base URL at this backend (e.g. `https://api.example.com`)
2. Add the frontend origin to `.env`:

```env
CORS_ALLOWED_ORIGINS=https://school.example.com,http://localhost:3000
```

## ✅ Development Checks

```bash
cd smartschool
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

## 🧹 Git Notes

Runtime/generated files are ignored and should never be committed:

```text
.env
env/
smartschool/db.sqlite3
smartschool/staticfiles/
.installer/
```

## 📄 License

Released under the **MIT License** — see [LICENSE](./LICENSE) for details.

---

<div align="center">
Made with ❤️ for schools — <a href="https://github.com/EXE88/smartschool-UI">frontend repo</a>
</div>
