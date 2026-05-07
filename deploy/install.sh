#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME_DEFAULT="smartschool"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/smartschool"
ENV_FILE="$PROJECT_ROOT/.env"
VENV_DIR="$PROJECT_ROOT/env"
GUNICORN_CONF="$PROJECT_ROOT/deploy/gunicorn/gunicorn.conf.py"
ROLLBACK_DIR="$PROJECT_ROOT/.deploy_rollback"
CREATED_LOG="$ROLLBACK_DIR/created.paths"
BACKUP_LOG="$ROLLBACK_DIR/backups.map"
ROLLBACK_ACTIVE=0
CREATED_PATHS=()
BACKUP_PATHS=()
SERVICE_NAME="${SERVICE_NAME:-$APP_NAME_DEFAULT}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

C_RESET='\033[0m'
C_BOLD='\033[1m'
C_RED='\033[31m'
C_GREEN='\033[32m'
C_YELLOW='\033[33m'
C_BLUE='\033[34m'
C_MAGENTA='\033[35m'
C_CYAN='\033[36m'

print_header() {
  clear || true
  echo -e "${C_CYAN}${C_BOLD}"
  echo "  ____                      _   ____       _                 _ "
  echo " / ___| _ __ ___   __ _ _ __| |_/ ___|  ___| |__   ___   ___ | |"
  echo " \___ \| '_ \\ _ \ / _\` | '__| __\___ \ / __| '_ \ / _ \ / _ \| |"
  echo "  ___) | | | | | | (_| | |  | |_ ___) | (__| | | | (_) | (_) | |"
  echo " |____/|_| |_| |_|\__,_|_|   \__|____/ \___|_| |_|\___/ \___/|_|"
  echo -e "${C_RESET}"
}

info() { echo -e "${C_BLUE}INFO${C_RESET} $*"; }
success() { echo -e "${C_GREEN}OK${C_RESET} $*"; }
warn() { echo -e "${C_YELLOW}WARN${C_RESET} $*"; }
fail() { echo -e "${C_RED}ERR${C_RESET} $*"; }

pause() {
  echo
  read -r -p "Press Enter to continue..." _ || true
}

require_linux() {
  if [[ "${OSTYPE:-}" != linux* ]]; then
    fail "This installer is intended for Linux production servers."
    exit 1
  fi
}

require_root_for_systemd() {
  if [[ "${EUID}" -ne 0 ]]; then
    fail "This action needs root privileges because it writes systemd files. Run with sudo."
    exit 1
  fi
}

backup_file() {
  local path="$1"
  [[ -e "$path" ]] || return 0
  mkdir -p "$ROLLBACK_DIR"
  local backup="$ROLLBACK_DIR/$(echo "$path" | sed 's#/#__#g').bak"
  cp -a "$path" "$backup"
  BACKUP_PATHS+=("$path::$backup")
  echo "$path::$backup" >> "$BACKUP_LOG"
}

track_created() {
  local path="$1"
  [[ -e "$path" ]] || CREATED_PATHS+=("$path")
  if [[ ! -e "$path" ]]; then
    mkdir -p "$ROLLBACK_DIR"
    echo "$path" >> "$CREATED_LOG"
  fi
}

rollback() {
  [[ "$ROLLBACK_ACTIVE" -eq 1 ]] || return 0
  warn "Rolling back partial installation..."

  if systemctl list-unit-files "${SERVICE_NAME}.service" >/dev/null 2>&1; then
    systemctl stop "$SERVICE_NAME" >/dev/null 2>&1 || true
    systemctl disable "$SERVICE_NAME" >/dev/null 2>&1 || true
  fi

  if [[ -f "$BACKUP_LOG" ]]; then
    while IFS= read -r item; do
      [[ -n "$item" ]] && BACKUP_PATHS+=("$item")
    done < "$BACKUP_LOG"
  fi

  for item in "${BACKUP_PATHS[@]:-}"; do
    local original="${item%%::*}"
    local backup="${item##*::}"
    [[ -e "$backup" ]] && cp -a "$backup" "$original"
  done

  if [[ -f "$CREATED_LOG" ]]; then
    while IFS= read -r path; do
      [[ -n "$path" ]] && CREATED_PATHS+=("$path")
    done < "$CREATED_LOG"
  fi

  for path in "${CREATED_PATHS[@]:-}"; do
    if [[ -e "$path" ]]; then
      rm -rf "$path"
    fi
  done

  systemctl daemon-reload >/dev/null 2>&1 || true
  warn "Rollback finished. You can run install again."
}

on_error() {
  local code=$?
  fail "Operation failed with exit code $code."
  rollback
  exit "$code"
}

on_interrupt() {
  fail "Operation interrupted by user."
  rollback
  exit 130
}

trap on_error ERR
trap on_interrupt INT TERM

prompt() {
  local label="$1"
  local default="${2:-}"
  local value
  if [[ -n "$default" ]]; then
    read -r -p "$label [$default]: " value || true
    echo "${value:-$default}"
  else
    read -r -p "$label: " value || true
    echo "$value"
  fi
}

configure_proxy() {
  echo -e "${C_MAGENTA}Network proxy setup${C_RESET}"
  read -r -p "Use proxy for downloads/install commands? [y/N]: " use_proxy || true
  if [[ ! "$use_proxy" =~ ^[Yy]$ ]]; then
    return 0
  fi

  local proxy_url no_proxy
  proxy_url="$(prompt 'Proxy URL (example: http://127.0.0.1:8080 or socks5://127.0.0.1:1080)' '')"
  if [[ -z "$proxy_url" ]]; then
    warn "Proxy was enabled but no URL was provided. Continuing without proxy."
    return 0
  fi

  no_proxy="$(prompt 'NO_PROXY hosts comma separated' 'localhost,127.0.0.1,::1')"

  export HTTP_PROXY="$proxy_url"
  export HTTPS_PROXY="$proxy_url"
  export ALL_PROXY="$proxy_url"
  export http_proxy="$proxy_url"
  export https_proxy="$proxy_url"
  export all_proxy="$proxy_url"
  export NO_PROXY="$no_proxy"
  export no_proxy="$no_proxy"
  export PIP_PROXY="$proxy_url"

  success "Proxy enabled for this installer run."
}

random_secret() {
  "$PYTHON_BIN" - <<'PY'
import secrets
print(secrets.token_urlsafe(50))
PY
}

write_env() {
  backup_file "$ENV_FILE"
  track_created "$ENV_FILE"

  local secret_key debug allowed_hosts cors_origins admin_path bind workers threads timeout graceful keepalive loglevel
  echo -e "${C_MAGENTA}Production environment setup${C_RESET}"
  secret_key="$(prompt 'SECRET_KEY (leave empty to generate)' '')"
  if [[ -z "$secret_key" ]]; then
    secret_key="$(random_secret)"
  fi
  debug="$(prompt 'DEBUG' 'False')"
  allowed_hosts="$(prompt 'ALLOWED_HOSTS comma separated' 'localhost,127.0.0.1')"
  cors_origins="$(prompt 'CORS_ALLOWED_ORIGINS comma separated' 'http://localhost:3000,http://127.0.0.1:3000')"
  admin_path="$(prompt 'Django admin path without leading/trailing slash' 'secure-admin')"
  bind="$(prompt 'Gunicorn bind' '0.0.0.0:8000')"
  workers="$(prompt 'Gunicorn workers' '3')"
  threads="$(prompt 'Gunicorn threads' '2')"
  timeout="$(prompt 'Gunicorn timeout' '120')"
  graceful="$(prompt 'Gunicorn graceful timeout' '30')"
  keepalive="$(prompt 'Gunicorn keepalive' '5')"
  loglevel="$(prompt 'Gunicorn log level' 'info')"

  cat > "$ENV_FILE" <<EOF
SECRET_KEY="$secret_key"
DEBUG="$debug"
ALLOWED_HOSTS="$allowed_hosts"
CORS_ALLOWED_ORIGINS="$cors_origins"
ADMIN_PATH="$admin_path"

GUNICORN_BIND="$bind"
GUNICORN_WORKERS="$workers"
GUNICORN_THREADS="$threads"
GUNICORN_TIMEOUT="$timeout"
GUNICORN_GRACEFUL_TIMEOUT="$graceful"
GUNICORN_KEEPALIVE="$keepalive"
GUNICORN_LOG_LEVEL="$loglevel"
EOF
  chmod 600 "$ENV_FILE" || true
  success "Wrote $ENV_FILE"
}

write_service() {
  backup_file "$SERVICE_FILE"
  track_created "$SERVICE_FILE"

  local run_user run_group
  run_user="$(prompt 'Linux user to run service' "$(id -un)")"
  run_group="$(id -gn "$run_user" 2>/dev/null || echo "$run_user")"

  cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=SmartSchool Gunicorn Service
After=network.target

[Service]
Type=simple
User=$run_user
Group=$run_group
WorkingDirectory=$BACKEND_DIR
Environment=PYTHONUNBUFFERED=1
Environment=DJANGO_ENV_FILE=$ENV_FILE
EnvironmentFile=$ENV_FILE
ExecStart=$VENV_DIR/bin/gunicorn --config $GUNICORN_CONF smartschool.wsgi:application
Restart=always
RestartSec=5
TimeoutStopSec=30
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
EOF
  chmod 644 "$SERVICE_FILE"
  success "Wrote $SERVICE_FILE"
}

ensure_python() {
  PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || true)}"
  if [[ -z "$PYTHON_BIN" ]]; then
    fail "python3 not found. Install python3 and python3-venv first."
    exit 1
  fi
}

install_app() {
  require_linux
  require_root_for_systemd
  print_header
  ROLLBACK_ACTIVE=1
  mkdir -p "$ROLLBACK_DIR"
  : > "$CREATED_LOG"
  : > "$BACKUP_LOG"
  ensure_python

  SERVICE_NAME="$(prompt 'Systemd service name' "$APP_NAME_DEFAULT")"
  SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

  info "Project root: $PROJECT_ROOT"
  info "Backend dir: $BACKEND_DIR"

  if [[ ! -f "$BACKEND_DIR/manage.py" ]]; then
    fail "manage.py not found at $BACKEND_DIR/manage.py"
    exit 1
  fi

  if [[ ! -d "$VENV_DIR" ]]; then
    track_created "$VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi

  configure_proxy

  local pip_proxy_args=()
  if [[ -n "${PIP_PROXY:-}" ]]; then
    pip_proxy_args=(--proxy "$PIP_PROXY")
  fi

  "$VENV_DIR/bin/python" -m pip install "${pip_proxy_args[@]}" --upgrade pip setuptools wheel
  "$VENV_DIR/bin/pip" install "${pip_proxy_args[@]}" -r "$PROJECT_ROOT/requirements.txt"

  PYTHON_BIN="$VENV_DIR/bin/python"
  write_env

  pushd "$BACKEND_DIR" >/dev/null
  DJANGO_ENV_FILE="$ENV_FILE" "$VENV_DIR/bin/python" manage.py check
  DJANGO_ENV_FILE="$ENV_FILE" "$VENV_DIR/bin/python" manage.py migrate
  DJANGO_ENV_FILE="$ENV_FILE" "$VENV_DIR/bin/python" manage.py collectstatic --noinput
  popd >/dev/null

  write_service
  systemctl daemon-reload
  systemctl enable "$SERVICE_NAME"
  systemctl restart "$SERVICE_NAME"

  ROLLBACK_ACTIVE=0
  rm -rf "$ROLLBACK_DIR"
  success "Installation completed. Service: $SERVICE_NAME"
  systemctl --no-pager status "$SERVICE_NAME" || true
}

status_app() {
  require_linux
  SERVICE_NAME="$(prompt 'Systemd service name' "$APP_NAME_DEFAULT")"
  systemctl --no-pager status "$SERVICE_NAME" || true
}

restart_app() {
  require_linux
  require_root_for_systemd
  SERVICE_NAME="$(prompt 'Systemd service name' "$APP_NAME_DEFAULT")"
  systemctl restart "$SERVICE_NAME"
  success "Restarted $SERVICE_NAME"
}

logs_app() {
  require_linux
  SERVICE_NAME="$(prompt 'Systemd service name' "$APP_NAME_DEFAULT")"
  journalctl -u "$SERVICE_NAME" -n 120 --no-pager || true
}

uninstall_app() {
  require_linux
  require_root_for_systemd
  print_header
  SERVICE_NAME="$(prompt 'Systemd service name' "$APP_NAME_DEFAULT")"
  SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

  warn "This will stop and remove the systemd service."
  read -r -p "Remove venv/staticfiles too? [y/N]: " remove_files || true
  read -r -p "Keep .env? [Y/n]: " keep_env || true

  systemctl stop "$SERVICE_NAME" >/dev/null 2>&1 || true
  systemctl disable "$SERVICE_NAME" >/dev/null 2>&1 || true
  rm -f "$SERVICE_FILE"
  systemctl daemon-reload

  if [[ "$remove_files" =~ ^[Yy]$ ]]; then
    rm -rf "$VENV_DIR" "$BACKEND_DIR/staticfiles"
  fi
  if [[ "$keep_env" =~ ^[Nn]$ ]]; then
    rm -f "$ENV_FILE"
  fi

  success "Uninstall finished. Database was not removed."
}

rollback_menu() {
  require_linux
  require_root_for_systemd
  if [[ ! -d "$ROLLBACK_DIR" ]]; then
    warn "No rollback snapshot found."
    return 0
  fi
  ROLLBACK_ACTIVE=1
  rollback
  ROLLBACK_ACTIVE=0
}

menu() {
  while true; do
    print_header
    echo -e "${C_BOLD}Project:${C_RESET} $PROJECT_ROOT"
    echo
    echo -e "${C_GREEN}1${C_RESET}) Install / Reinstall production service"
    echo -e "${C_GREEN}2${C_RESET}) Service status"
    echo -e "${C_GREEN}3${C_RESET}) Restart service"
    echo -e "${C_GREEN}4${C_RESET}) Show logs"
    echo -e "${C_GREEN}5${C_RESET}) Uninstall service"
    echo -e "${C_GREEN}6${C_RESET}) Rollback last failed install"
    echo -e "${C_GREEN}0${C_RESET}) Exit"
    echo
    read -r -p "Choose: " choice || true
    case "$choice" in
      1) install_app; pause ;;
      2) status_app; pause ;;
      3) restart_app; pause ;;
      4) logs_app; pause ;;
      5) uninstall_app; pause ;;
      6) rollback_menu; pause ;;
      0) exit 0 ;;
      *) warn "Invalid choice"; pause ;;
    esac
  done
}

case "${1:-menu}" in
  install) install_app ;;
  status) status_app ;;
  restart) restart_app ;;
  logs) logs_app ;;
  uninstall) uninstall_app ;;
  rollback) rollback_menu ;;
  menu|*) menu ;;
esac
