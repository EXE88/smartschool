#!/usr/bin/env bash
#
# SmartSchool — interactive installer & manager
#
#   sudo ./install.sh            interactive menu
#   sudo ./install.sh install    full installation
#   sudo ./install.sh <action>   run a single action (see ./install.sh help)
#
# Features:
#   * colorful interactive menu
#   * automatic rollback on failure or Ctrl+C
#   * guided .env configuration
#   * systemd service (auto-restart, survives reboots)
#   * every section re-runnable after install (no full reinstall needed)
#   * optional proxy for downloads
#   * demo data seeding / removal

set -o pipefail

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
DJANGO_DIR="$PROJECT_DIR/smartschool"
VENV_DIR="$PROJECT_DIR/env"
ENV_FILE="$PROJECT_DIR/.env"
ENV_SAMPLE="$PROJECT_DIR/.env.sample"
REQ_FILE="$PROJECT_DIR/requirements.txt"
GUNICORN_CONF="$DJANGO_DIR/gunicorn.conf.py"

SERVICE_NAME="smartschool"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

STATE_DIR="$PROJECT_DIR/.installer"
MANIFEST="$STATE_DIR/rollback.manifest"
BACKUP_DIR="$STATE_DIR/backups"
PROXY_CONF="$STATE_DIR/proxy.conf"
INSTALLED_MARKER="$STATE_DIR/installed"

PYTHON_BIN=""
INSTALL_IN_PROGRESS=0

# ---------------------------------------------------------------------------
# Colors & output helpers
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
    C_RESET=$'\033[0m';  C_BOLD=$'\033[1m';   C_DIM=$'\033[2m'
    C_RED=$'\033[31m';   C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'
    C_BLUE=$'\033[34m';  C_MAGENTA=$'\033[35m'; C_CYAN=$'\033[36m'
else
    C_RESET=""; C_BOLD=""; C_DIM=""; C_RED=""; C_GREEN=""; C_YELLOW=""
    C_BLUE=""; C_MAGENTA=""; C_CYAN=""
fi

info()  { printf '%s\n' "${C_CYAN}[i]${C_RESET} $*"; }
ok()    { printf '%s\n' "${C_GREEN}[✓]${C_RESET} $*"; }
warn()  { printf '%s\n' "${C_YELLOW}[!]${C_RESET} $*"; }
err()   { printf '%s\n' "${C_RED}[✗]${C_RESET} $*" >&2; }
step()  { printf '\n%s\n' "${C_BOLD}${C_BLUE}==>${C_RESET} ${C_BOLD}$*${C_RESET}"; }

banner() {
    printf '%s' "${C_MAGENTA}${C_BOLD}"
    cat <<'EOF'

  ____                       _   ____       _                 _
 / ___| _ __ ___   __ _ _ __| |_/ ___|  ___| |__   ___   ___ | |
 \___ \| '_ ` _ \ / _` | '__| __\___ \ / __| '_ \ / _ \ / _ \| |
  ___) | | | | | | (_| | |  | |_ ___) | (__| | | | (_) | (_) | |
 |____/|_| |_| |_|\__,_|_|   \__|____/ \___|_| |_|\___/ \___/|_|

EOF
    printf '%s' "${C_RESET}"
    printf '        %s\n\n' "${C_DIM}Django backend — installer & manager${C_RESET}"
}

# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------
ask() {
    # ask "question" "default" -> REPLY_VALUE
    local question="$1" default="${2:-}" answer
    if [ -n "$default" ]; then
        printf '%s' "${C_CYAN}?${C_RESET} ${question} ${C_DIM}[${default}]${C_RESET}: " > /dev/tty
    else
        printf '%s' "${C_CYAN}?${C_RESET} ${question}: " > /dev/tty
    fi
    IFS= read -r answer < /dev/tty
    REPLY_VALUE="${answer:-$default}"
}

ask_yesno() {
    # ask_yesno "question" "y|n" -> return 0 for yes
    local question="$1" default="${2:-y}" hint answer
    if [ "$default" = "y" ]; then hint="Y/n"; else hint="y/N"; fi
    while true; do
        printf '%s' "${C_CYAN}?${C_RESET} ${question} ${C_DIM}[${hint}]${C_RESET}: " > /dev/tty
        IFS= read -r answer < /dev/tty
        answer="${answer:-$default}"
        case "$answer" in
            [Yy]*) return 0 ;;
            [Nn]*) return 1 ;;
        esac
    done
}

pause() {
    printf '\n%s' "${C_DIM}Press Enter to continue...${C_RESET}" > /dev/tty
    IFS= read -r _ < /dev/tty
}

# ---------------------------------------------------------------------------
# Environment checks
# ---------------------------------------------------------------------------
require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        err "This action needs root. Re-run with: sudo ./install.sh $*"
        exit 1
    fi
}

have_systemd() { command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; }

detect_python() {
    if [ -x "$VENV_DIR/bin/python" ]; then
        PYTHON_BIN="$VENV_DIR/bin/python"
        return
    fi
    for candidate in python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            PYTHON_BIN="$(command -v "$candidate")"
            return
        fi
    done
    err "Python 3 was not found. Install it first (e.g. apt install python3 python3-venv)."
    exit 1
}

venv_python() { printf '%s' "$VENV_DIR/bin/python"; }

require_venv() {
    if [ ! -x "$(venv_python)" ]; then
        err "Virtual environment not found at $VENV_DIR — run the installation first."
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Proxy support
# ---------------------------------------------------------------------------
PROXY_URL=""

load_proxy() { [ -f "$PROXY_CONF" ] && PROXY_URL="$(cat "$PROXY_CONF")"; }

apply_proxy_env() {
    if [ -n "$PROXY_URL" ]; then
        export HTTP_PROXY="$PROXY_URL" HTTPS_PROXY="$PROXY_URL" ALL_PROXY="$PROXY_URL"
        export http_proxy="$PROXY_URL" https_proxy="$PROXY_URL" all_proxy="$PROXY_URL"
        export NO_PROXY="127.0.0.1,localhost" no_proxy="127.0.0.1,localhost"
    fi
}

configure_proxy() {
    step "Proxy configuration"
    load_proxy
    if [ -n "$PROXY_URL" ]; then
        info "Current proxy: ${C_BOLD}${PROXY_URL}${C_RESET}"
        if ask_yesno "Remove the configured proxy?" "n"; then
            rm -f "$PROXY_CONF"
            PROXY_URL=""
            ok "Proxy removed."
            return
        fi
    fi
    if ask_yesno "Use a proxy for downloads (pip, etc.)?" "n"; then
        ask "Proxy URL (e.g. http://127.0.0.1:8080 or socks5://127.0.0.1:1080)" "$PROXY_URL"
        PROXY_URL="$REPLY_VALUE"
        if [ -n "$PROXY_URL" ]; then
            mkdir -p "$STATE_DIR"
            printf '%s' "$PROXY_URL" > "$PROXY_CONF"
            ok "Proxy saved: $PROXY_URL"
        fi
    fi
    apply_proxy_env
}

pip_install() {
    local pip_args=()
    [ -n "$PROXY_URL" ] && pip_args+=(--proxy "$PROXY_URL")
    "$(venv_python)" -m pip install "${pip_args[@]}" "$@"
}

# ---------------------------------------------------------------------------
# Rollback engine
#
# Every change made during installation is recorded in a manifest:
#   created|<path>            -> removed on rollback
#   backup|<path>|<backup>    -> restored on rollback
#   service|<name>            -> stopped/disabled/removed on rollback
# The manifest is replayed in reverse order.
# ---------------------------------------------------------------------------
rollback_begin() {
    mkdir -p "$STATE_DIR" "$BACKUP_DIR"
    : > "$MANIFEST"
}

record_created() { printf 'created|%s\n' "$1" >> "$MANIFEST"; }
record_service() { printf 'service|%s\n' "$1" >> "$MANIFEST"; }

backup_file() {
    # backup_file <path> — snapshot an existing file before we overwrite it
    local path="$1"
    [ -e "$path" ] || return 0
    mkdir -p "$STATE_DIR" "$BACKUP_DIR"
    local name
    name="$(printf '%s' "$path" | tr '/' '_')"
    local dest="$BACKUP_DIR/${name}.$(date +%s%N)"
    cp -a "$path" "$dest"
    printf 'backup|%s|%s\n' "$path" "$dest" >> "$MANIFEST"
}

do_rollback() {
    if [ ! -s "$MANIFEST" ]; then
        info "Nothing to roll back (manifest is empty)."
        return 0
    fi
    warn "Rolling back changes..."
    # replay in reverse order
    tac "$MANIFEST" | while IFS='|' read -r kind a b; do
        case "$kind" in
            created)
                if [ -e "$a" ]; then
                    rm -rf "$a"
                    info "Removed: $a"
                fi
                ;;
            backup)
                if [ -e "$b" ]; then
                    cp -a "$b" "$a"
                    info "Restored: $a"
                fi
                ;;
            service)
                if have_systemd; then
                    systemctl stop "$a" >/dev/null 2>&1 || true
                    systemctl disable "$a" >/dev/null 2>&1 || true
                    rm -f "/etc/systemd/system/${a}.service"
                    systemctl daemon-reload >/dev/null 2>&1 || true
                    info "Service removed: $a"
                fi
                ;;
        esac
    done
    : > "$MANIFEST"
    ok "Rollback finished. You can safely run the installer again."
}

rollback_commit() {
    # Installation succeeded — keep a log copy, clear the active manifest
    [ -s "$MANIFEST" ] && cp "$MANIFEST" "$STATE_DIR/last-install.log"
    : > "$MANIFEST"
}

on_install_interrupt() {
    trap - INT TERM ERR
    echo
    err "Installation interrupted."
    do_rollback
    exit 130
}

on_install_error() {
    trap - INT TERM ERR
    err "Installation failed at: ${CURRENT_STEP:-unknown step}"
    do_rollback
    exit 1
}

run_step() {
    # run_step "description" command...
    CURRENT_STEP="$1"; shift
    step "$CURRENT_STEP"
    "$@" || on_install_error
}

# ---------------------------------------------------------------------------
# .env handling
# ---------------------------------------------------------------------------
generate_secret_key() {
    "$PYTHON_BIN" - <<'PYEOF'
import secrets, string
alphabet = string.ascii_letters + string.digits + "-_"
print("".join(secrets.choice(alphabet) for _ in range(64)))
PYEOF
}

get_env_var() {
    # get_env_var KEY DEFAULT
    local key="$1" default="${2:-}"
    if [ -f "$ENV_FILE" ]; then
        local line
        line="$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1)"
        if [ -n "$line" ]; then
            printf '%s' "${line#*=}"
            return
        fi
    fi
    printf '%s' "$default"
}

set_env_var() {
    # set_env_var KEY VALUE — update in place or append
    local key="$1" value="$2"
    touch "$ENV_FILE"
    if grep -qE "^${key}=" "$ENV_FILE"; then
        # use awk to avoid sed delimiter issues with URLs
        awk -v k="$key" -v v="$value" -F'=' \
            'BEGIN{OFS="="} $1==k{print k"="v; next} {print}' \
            "$ENV_FILE" > "$ENV_FILE.tmp" && mv "$ENV_FILE.tmp" "$ENV_FILE"
    else
        printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
    fi
}

configure_env() {
    step "Configure .env"
    detect_python

    local created_new=0
    if [ -f "$ENV_FILE" ]; then
        info "An existing .env was found — current values are used as defaults."
        backup_file "$ENV_FILE"
    else
        created_new=1
    fi

    # --- Django ---
    printf '\n%s\n' "${C_BOLD}Django settings${C_RESET}"

    local secret
    secret="$(get_env_var SECRET_KEY)"
    if [ -z "$secret" ] || [ "$secret" = "change-me" ]; then
        if ask_yesno "Generate a random SECRET_KEY automatically?" "y"; then
            secret="$(generate_secret_key)"
            ok "SECRET_KEY generated."
        else
            ask "SECRET_KEY" ""
            secret="$REPLY_VALUE"
        fi
    else
        if ask_yesno "Keep the existing SECRET_KEY?" "y"; then
            :
        else
            secret="$(generate_secret_key)"
            ok "New SECRET_KEY generated."
        fi
    fi

    local debug
    if ask_yesno "Enable DEBUG mode? (not recommended for production)" "n"; then
        debug="True"
    else
        debug="False"
    fi

    ask "ALLOWED_HOSTS (comma separated domains/IPs)" "$(get_env_var ALLOWED_HOSTS "127.0.0.1,localhost")"
    local allowed_hosts="$REPLY_VALUE"

    ask "CORS_ALLOWED_ORIGINS (comma separated, include your frontend origin)" \
        "$(get_env_var CORS_ALLOWED_ORIGINS "http://localhost:3000,http://127.0.0.1:3000")"
    local cors="$REPLY_VALUE"

    ask "ADMIN_PATH (Django admin URL path, avoid 'admin' in production)" \
        "$(get_env_var ADMIN_PATH "secure-admin")"
    local admin_path="$REPLY_VALUE"

    # --- Gunicorn ---
    printf '\n%s\n' "${C_BOLD}Gunicorn settings${C_RESET}"
    ask "Bind address (host:port)"          "$(get_env_var GUNICORN_BIND "0.0.0.0:8000")";        local g_bind="$REPLY_VALUE"
    ask "Workers"                           "$(get_env_var GUNICORN_WORKERS "3")";                 local g_workers="$REPLY_VALUE"
    ask "Threads per worker"                "$(get_env_var GUNICORN_THREADS "2")";                 local g_threads="$REPLY_VALUE"
    ask "Request timeout (seconds)"         "$(get_env_var GUNICORN_TIMEOUT "120")";               local g_timeout="$REPLY_VALUE"
    ask "Graceful shutdown timeout (sec)"   "$(get_env_var GUNICORN_GRACEFUL_TIMEOUT "30")";       local g_grace="$REPLY_VALUE"
    ask "Keep-alive (seconds)"              "$(get_env_var GUNICORN_KEEPALIVE "5")";               local g_keep="$REPLY_VALUE"
    ask "Log level (debug/info/warning/error)" "$(get_env_var GUNICORN_LOG_LEVEL "info")";         local g_log="$REPLY_VALUE"

    # --- Write file ---
    [ "$created_new" -eq 1 ] && record_created "$ENV_FILE"
    cat > "$ENV_FILE" <<EOF
SECRET_KEY=${secret}
DEBUG=${debug}
ALLOWED_HOSTS=${allowed_hosts}
CORS_ALLOWED_ORIGINS=${cors}
ADMIN_PATH=${admin_path}

GUNICORN_BIND=${g_bind}
GUNICORN_WORKERS=${g_workers}
GUNICORN_THREADS=${g_threads}
GUNICORN_TIMEOUT=${g_timeout}
GUNICORN_GRACEFUL_TIMEOUT=${g_grace}
GUNICORN_KEEPALIVE=${g_keep}
GUNICORN_LOG_LEVEL=${g_log}
EOF
    chmod 600 "$ENV_FILE" 2>/dev/null || true
    ok ".env written to $ENV_FILE"

    maybe_restart_service
}

configure_gunicorn() {
    step "Gunicorn settings"
    if [ ! -f "$ENV_FILE" ]; then
        err ".env not found — run '.env configuration' first."
        return 1
    fi
    backup_file "$ENV_FILE"
    ask "Bind address (host:port)"          "$(get_env_var GUNICORN_BIND "0.0.0.0:8000")";      set_env_var GUNICORN_BIND "$REPLY_VALUE"
    ask "Workers"                           "$(get_env_var GUNICORN_WORKERS "3")";               set_env_var GUNICORN_WORKERS "$REPLY_VALUE"
    ask "Threads per worker"                "$(get_env_var GUNICORN_THREADS "2")";               set_env_var GUNICORN_THREADS "$REPLY_VALUE"
    ask "Request timeout (seconds)"         "$(get_env_var GUNICORN_TIMEOUT "120")";             set_env_var GUNICORN_TIMEOUT "$REPLY_VALUE"
    ask "Log level (debug/info/warning/error)" "$(get_env_var GUNICORN_LOG_LEVEL "info")";       set_env_var GUNICORN_LOG_LEVEL "$REPLY_VALUE"
    ok "Gunicorn settings updated."
    maybe_restart_service
}

# ---------------------------------------------------------------------------
# Installation steps
# ---------------------------------------------------------------------------
create_venv() {
    if [ -x "$(venv_python)" ]; then
        info "Reusing existing virtual environment: $VENV_DIR"
        return 0
    fi
    detect_python
    [ -d "$VENV_DIR" ] || record_created "$VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    ok "Virtual environment created at $VENV_DIR"
}

install_requirements() {
    require_venv
    load_proxy; apply_proxy_env
    pip_install --upgrade pip
    pip_install -r "$REQ_FILE"
    ok "Dependencies installed."
}

manage_py() {
    require_venv
    ( cd "$DJANGO_DIR" && "$(venv_python)" manage.py "$@" )
}

run_migrations() {
    step "Database migrations"
    [ -f "$DJANGO_DIR/db.sqlite3" ] && backup_file "$DJANGO_DIR/db.sqlite3"
    manage_py migrate --noinput
    ok "Migrations applied."
}

run_collectstatic() {
    step "Collect static files"
    manage_py collectstatic --noinput
    ok "Static files collected."
}

run_check() {
    step "Django system check"
    manage_py check
    ok "Checks passed."
}

create_superuser() {
    step "Create Django superuser"
    manage_py createsuperuser
}

# ---------------------------------------------------------------------------
# systemd service
# ---------------------------------------------------------------------------
service_user_prompt() {
    local default_user="${SUDO_USER:-$(id -un)}"
    ask "System user to run the service as" "$default_user"
    SERVICE_USER="$REPLY_VALUE"
    if ! id "$SERVICE_USER" >/dev/null 2>&1; then
        err "User '$SERVICE_USER' does not exist."
        return 1
    fi
}

create_service() {
    step "Create systemd service"
    if ! have_systemd; then
        warn "systemd is not available on this system — skipping service creation."
        return 0
    fi
    require_root "service"
    service_user_prompt || return 1

    local existed=0
    [ -f "$SERVICE_FILE" ] && { existed=1; backup_file "$SERVICE_FILE"; }

    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=SmartSchool Django backend (Gunicorn)
After=network.target

[Service]
Type=exec
User=${SERVICE_USER}
WorkingDirectory=${DJANGO_DIR}
EnvironmentFile=-${ENV_FILE}
ExecStart=${VENV_DIR}/bin/gunicorn -c ${GUNICORN_CONF} smartschool.wsgi:application
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal

# Hardening
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
    [ "$existed" -eq 0 ] && record_service "$SERVICE_NAME"

    # make sure the service user can read/write the project
    if [ -n "${SERVICE_USER:-}" ] && [ "$SERVICE_USER" != "root" ]; then
        chown -R "$SERVICE_USER" "$PROJECT_DIR" 2>/dev/null || true
    fi

    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME" >/dev/null
    systemctl restart "$SERVICE_NAME"
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        ok "Service '$SERVICE_NAME' is running and enabled at boot."
    else
        err "Service failed to start. Recent logs:"
        journalctl -u "$SERVICE_NAME" -n 20 --no-pager || true
        return 1
    fi
}

maybe_restart_service() {
    if have_systemd && systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        if ask_yesno "Restart the '$SERVICE_NAME' service to apply changes?" "y"; then
            systemctl restart "$SERVICE_NAME" && ok "Service restarted."
        fi
    fi
}

service_action() {
    if ! have_systemd; then
        err "systemd is not available on this system."
        return 1
    fi
    case "$1" in
        status)  systemctl status "$SERVICE_NAME" --no-pager || true ;;
        start)   systemctl start "$SERVICE_NAME"   && ok "Service started." ;;
        stop)    systemctl stop "$SERVICE_NAME"    && ok "Service stopped." ;;
        restart) systemctl restart "$SERVICE_NAME" && ok "Service restarted." ;;
        enable)  systemctl enable "$SERVICE_NAME"  && ok "Service enabled at boot." ;;
        disable) systemctl disable "$SERVICE_NAME" && ok "Service disabled at boot." ;;
        logs)    journalctl -u "$SERVICE_NAME" -n 100 -f ;;
    esac
}

# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------
seed_demo_data() {
    step "Seed demo data"
    manage_py shell -c "exec(open('seed_demo_data.py', encoding='utf-8-sig').read())"
    ok "Demo data seeded. Sample logins — username: 1 / password: 1, username: 2 / password: 2"
}

remove_demo_data() {
    step "Remove demo data"
    warn "This deletes all demo users (marked with last_name='seed') and demo classes/lessons."
    ask_yesno "Continue?" "n" || { info "Cancelled."; return 0; }
    manage_py shell <<'PYEOF'
from django.contrib.auth.models import User
from django.db import transaction

from basemodels.models import Classes, Grades, Lessons, Subjects
from weeklyschedules.models import WeeklySchedule

DEMO_SUBJECTS = ["ریاضی", "تجربی"]
DEMO_CLASSES = [f"یازدهم {s}" for s in DEMO_SUBJECTS]

with transaction.atomic():
    demo_classes = Classes.objects.filter(name__in=DEMO_CLASSES)
    ws = WeeklySchedule.objects.filter(classobj__in=demo_classes).delete()
    users = User.objects.filter(last_name="seed").delete()
    lessons = Lessons.objects.filter(subject__name__in=DEMO_SUBJECTS).delete()
    classes = demo_classes.delete()
    subjects = Subjects.objects.filter(
        name__in=DEMO_SUBJECTS, classes__isnull=True, lessons__isnull=True
    ).delete()
    grades = Grades.objects.filter(
        name="یازدهم", classes__isnull=True, lessons__isnull=True
    ).delete()

print("Removed:")
print(f"  users (cascade): {users[0]}")
print(f"  weekly schedules: {ws[0]}")
print(f"  lessons: {lessons[0]}")
print(f"  classes: {classes[0]}")
print(f"  subjects: {subjects[0]}")
print(f"  grades: {grades[0]}")
PYEOF
    ok "Demo data removed."
}

# ---------------------------------------------------------------------------
# Full install / uninstall
# ---------------------------------------------------------------------------
full_install() {
    require_root "install"
    banner
    info "Project directory: ${C_BOLD}${PROJECT_DIR}${C_RESET}"

    INSTALL_IN_PROGRESS=1
    rollback_begin
    trap on_install_interrupt INT TERM

    configure_proxy

    run_step "Create virtual environment"  create_venv
    run_step "Install dependencies"        install_requirements

    CURRENT_STEP="Configure .env"
    configure_env || on_install_error

    CURRENT_STEP="Django system check";     run_check          || on_install_error
    CURRENT_STEP="Database migrations";     run_migrations     || on_install_error
    CURRENT_STEP="Collect static files";    run_collectstatic  || on_install_error

    if ask_yesno "Create a Django superuser now?" "y"; then
        CURRENT_STEP="Create superuser"
        create_superuser || on_install_error
    fi

    if ask_yesno "Seed demo data for testing?" "n"; then
        CURRENT_STEP="Seed demo data"
        seed_demo_data || on_install_error
    fi

    if have_systemd; then
        CURRENT_STEP="Create systemd service"
        create_service || on_install_error
    else
        warn "systemd not detected — start the app manually with:"
        printf '    %s\n' "cd $DJANGO_DIR && $VENV_DIR/bin/gunicorn -c $GUNICORN_CONF smartschool.wsgi:application"
    fi

    trap - INT TERM
    INSTALL_IN_PROGRESS=0
    rollback_commit
    date > "$INSTALLED_MARKER"

    local bind
    bind="$(get_env_var GUNICORN_BIND "0.0.0.0:8000")"
    echo
    ok "${C_BOLD}Installation completed successfully!${C_RESET}"
    printf '\n'
    printf '  %s\n' "API docs:    ${C_CYAN}http://${bind}/api/docs/${C_RESET}"
    printf '  %s\n' "Admin panel: ${C_CYAN}http://${bind}/$(get_env_var ADMIN_PATH "secure-admin")/${C_RESET}"
    printf '  %s\n' "Service:     ${C_CYAN}systemctl status ${SERVICE_NAME}${C_RESET}"
    printf '\n'
    info "Re-run ${C_BOLD}sudo ./install.sh${C_RESET} anytime to manage individual sections."
}

uninstall() {
    require_root "uninstall"
    step "Uninstall SmartSchool"
    warn "This removes the systemd service and optionally the venv, .env, static files and database."
    ask_yesno "Continue with uninstall?" "n" || { info "Cancelled."; return 0; }

    if have_systemd && [ -f "$SERVICE_FILE" ]; then
        systemctl stop "$SERVICE_NAME"    >/dev/null 2>&1 || true
        systemctl disable "$SERVICE_NAME" >/dev/null 2>&1 || true
        rm -f "$SERVICE_FILE"
        systemctl daemon-reload
        ok "systemd service removed."
    fi

    ask_yesno "Remove the virtual environment ($VENV_DIR)?" "y" && rm -rf "$VENV_DIR" && ok "venv removed."
    ask_yesno "Remove .env?" "n" && rm -f "$ENV_FILE" && ok ".env removed."
    ask_yesno "Remove collected static files?" "y" && rm -rf "$DJANGO_DIR/staticfiles" && ok "staticfiles removed."
    if [ -f "$DJANGO_DIR/db.sqlite3" ]; then
        ask_yesno "${C_RED}Delete the database (db.sqlite3)? This cannot be undone!${C_RESET}" "n" \
            && rm -f "$DJANGO_DIR/db.sqlite3" && ok "Database deleted."
    fi
    rm -f "$INSTALLED_MARKER"
    ok "Uninstall finished."
}

# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------
service_menu() {
    while true; do
        printf '\n%s\n' "${C_BOLD}${C_MAGENTA}── Service management ─────────────────────${C_RESET}"
        printf '  %s\n' "${C_CYAN}1)${C_RESET} Status"
        printf '  %s\n' "${C_CYAN}2)${C_RESET} Start"
        printf '  %s\n' "${C_CYAN}3)${C_RESET} Stop"
        printf '  %s\n' "${C_CYAN}4)${C_RESET} Restart"
        printf '  %s\n' "${C_CYAN}5)${C_RESET} Live logs (Ctrl+C to exit logs)"
        printf '  %s\n' "${C_CYAN}6)${C_RESET} Enable at boot"
        printf '  %s\n' "${C_CYAN}7)${C_RESET} Disable at boot"
        printf '  %s\n' "${C_CYAN}8)${C_RESET} Recreate service file"
        printf '  %s\n' "${C_CYAN}0)${C_RESET} Back"
        ask "Select" ""
        case "$REPLY_VALUE" in
            1) service_action status ;;
            2) service_action start ;;
            3) service_action stop ;;
            4) service_action restart ;;
            5) service_action logs ;;
            6) service_action enable ;;
            7) service_action disable ;;
            8) create_service ;;
            0) return ;;
        esac
    done
}

demo_menu() {
    while true; do
        printf '\n%s\n' "${C_BOLD}${C_MAGENTA}── Demo data ──────────────────────────────${C_RESET}"
        printf '  %s\n' "${C_CYAN}1)${C_RESET} Seed demo data"
        printf '  %s\n' "${C_CYAN}2)${C_RESET} Remove demo data"
        printf '  %s\n' "${C_CYAN}0)${C_RESET} Back"
        ask "Select" ""
        case "$REPLY_VALUE" in
            1) seed_demo_data; pause ;;
            2) remove_demo_data; pause ;;
            0) return ;;
        esac
    done
}

main_menu() {
    while true; do
        clear 2>/dev/null || true
        banner
        if [ -f "$INSTALLED_MARKER" ]; then
            printf '  %s\n' "${C_GREEN}● Installed${C_RESET} ${C_DIM}($(cat "$INSTALLED_MARKER"))${C_RESET}"
        else
            printf '  %s\n' "${C_YELLOW}○ Not installed yet${C_RESET}"
        fi
        if have_systemd; then
            if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
                printf '  %s\n' "${C_GREEN}● Service running${C_RESET} ${C_DIM}(${SERVICE_NAME})${C_RESET}"
            else
                printf '  %s\n' "${C_RED}○ Service not running${C_RESET}"
            fi
        fi
        printf '\n%s\n' "${C_BOLD}${C_MAGENTA}┌─ Main menu ───────────────────────────────┐${C_RESET}"
        printf '  %s\n' "${C_CYAN} 1)${C_RESET} Full installation"
        printf '  %s\n' "${C_CYAN} 2)${C_RESET} Configure .env (all settings)"
        printf '  %s\n' "${C_CYAN} 3)${C_RESET} Configure Gunicorn only"
        printf '  %s\n' "${C_CYAN} 4)${C_RESET} Service management (systemd)"
        printf '  %s\n' "${C_CYAN} 5)${C_RESET} Run migrations"
        printf '  %s\n' "${C_CYAN} 6)${C_RESET} Collect static files"
        printf '  %s\n' "${C_CYAN} 7)${C_RESET} Create superuser"
        printf '  %s\n' "${C_CYAN} 8)${C_RESET} Demo data (seed / remove)"
        printf '  %s\n' "${C_CYAN} 9)${C_RESET} Reinstall dependencies"
        printf '  %s\n' "${C_CYAN}10)${C_RESET} Proxy configuration"
        printf '  %s\n' "${C_CYAN}11)${C_RESET} Rollback last failed installation"
        printf '  %s\n' "${C_CYAN}12)${C_RESET} Uninstall"
        printf '  %s\n' "${C_CYAN} 0)${C_RESET} Exit"
        printf '%s\n' "${C_BOLD}${C_MAGENTA}└───────────────────────────────────────────┘${C_RESET}"
        ask "Select an option" ""
        case "$REPLY_VALUE" in
            1)  full_install; pause ;;
            2)  configure_env; pause ;;
            3)  configure_gunicorn; pause ;;
            4)  service_menu ;;
            5)  run_migrations; pause ;;
            6)  run_collectstatic; pause ;;
            7)  create_superuser; pause ;;
            8)  demo_menu ;;
            9)  load_proxy; apply_proxy_env; install_requirements; pause ;;
            10) configure_proxy; pause ;;
            11) do_rollback; pause ;;
            12) uninstall; pause ;;
            0)  exit 0 ;;
        esac
    done
}

usage() {
    banner
    cat <<EOF
Usage: sudo ./install.sh [command]

Commands:
  (no command)   interactive menu
  install        full installation (venv, deps, .env, migrate, static, service)
  env            configure .env interactively
  gunicorn       configure Gunicorn settings
  deps           (re)install Python dependencies
  migrate        run database migrations
  collectstatic  collect static files
  superuser      create a Django superuser
  demo-seed      seed demo data
  demo-remove    remove demo data
  status | start | stop | restart | logs
                 manage the systemd service
  service        (re)create the systemd service file
  proxy          configure download proxy
  rollback       roll back a failed/interrupted installation
  uninstall      remove service and optionally venv/.env/static/db
  help           show this help
EOF
}

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
main() {
    cd "$PROJECT_DIR"
    load_proxy
    apply_proxy_env

    case "${1:-menu}" in
        menu)          main_menu ;;
        install)       full_install ;;
        env)           configure_env ;;
        gunicorn)      configure_gunicorn ;;
        deps)          install_requirements ;;
        migrate)       run_migrations ;;
        collectstatic) run_collectstatic ;;
        superuser)     create_superuser ;;
        demo-seed)     seed_demo_data ;;
        demo-remove)   remove_demo_data ;;
        status|start|stop|restart|logs) service_action "$1" ;;
        service)       create_service ;;
        proxy)         configure_proxy ;;
        rollback)      do_rollback ;;
        uninstall)     uninstall ;;
        help|-h|--help) usage ;;
        *) err "Unknown command: $1"; usage; exit 1 ;;
    esac
}

main "$@"
