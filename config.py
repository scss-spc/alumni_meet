import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-scss-jnu-alumni-2026")
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    # TiDB Database Configuration
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.environ.get("DB_PORT", 4000))
    DB_NAME = os.environ.get("DB_NAME", "alumni_meet")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_SSL_CA = os.environ.get("DB_SSL_CA")

    # Google Form & Storage Integration
    GOOGLE_FORM_URL = os.environ.get(
        "GOOGLE_FORM_URL",
        "https://docs.google.com/forms/d/e/1FAIpQLScssJnuAlumniMeet2026/viewform"
    )
    GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
    GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
    GOOGLE_SHEET_NAME = os.environ.get("GOOGLE_SHEET_NAME", "Form Responses 1")
    GOOGLE_SHEET_CSV_URL = os.environ.get("GOOGLE_SHEET_CSV_URL", "")
    GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    SYNC_INTERVAL_HOURS = int(os.environ.get("SYNC_INTERVAL_HOURS", 24))
    AUTO_SYNC_ENABLED = os.environ.get("AUTO_SYNC_ENABLED", "True").lower() in ("true", "1", "yes")

    # Default Event Context
    CURRENT_MEET_ID = int(os.environ.get("CURRENT_MEET_ID", 1))

    # Initial Admin Seed
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@scss.jnu.ac.in")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "AdminPassword2026!")
    ADMIN_NAME = os.environ.get("ADMIN_NAME", "SC&SS Organizer Admin")

    # Configurable Admin Path Prefix (e.g. /admin, /manage, /secret-portal)
    _raw_admin_path = os.environ.get("ADMIN_PATH_PREFIX", "/admin").strip()
    if not _raw_admin_path.startswith("/"):
        _raw_admin_path = "/" + _raw_admin_path
    if len(_raw_admin_path) > 1 and _raw_admin_path.endswith("/"):
        _raw_admin_path = _raw_admin_path.rstrip("/")
    ADMIN_PATH_PREFIX = _raw_admin_path
