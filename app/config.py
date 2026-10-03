import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cadence:cadence@localhost:5433/cadence")
SOURCE = os.getenv("SOURCE", "local")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "")
# On Render the service-account JSON is passed as an env var instead of a file.
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
LOCAL_SOURCE_DIR = os.getenv("LOCAL_SOURCE_DIR", "./sample_drive")
SYNC_INTERVAL_HOURS = float(os.getenv("SYNC_INTERVAL_HOURS", "12"))
# Shared label password; login is disabled when unset (local dev).
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-only-secret")

# Sheet names must match the client templates exactly (note the trailing spaces).
SHEET_NAMES = {
    "spectacle": "RevenuDepenses",
    "album_expenses": "Depenses ",
    "album_revenues": "Revenus ",
    "fixe": "fixe",
}
