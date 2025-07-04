import tempfile
import os
import sys
import re
import os   
from dotenv import load_dotenv
load_dotenv()

#tempfile path
TMP_DIR = tempfile.gettempdir()
OUTPUT_CSV_DIR = os.path.join(TMP_DIR, "output_csv")
os.makedirs(OUTPUT_CSV_DIR, exist_ok=True)
def tmp_path(filename):
    return os.path.join(TMP_DIR, filename)

def sanitize_filename(filename):
    # Remove or replace characters not allowed in filenames
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def get_pdf_output_dir(pdf_name):
    """Return (and create if needed) the output_csv subfolder for a given PDF name."""
    folder_name = sanitize_filename(pdf_name.rsplit('.', 1)[0])
    output_dir = os.path.join(OUTPUT_CSV_DIR, folder_name)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir
# Directory where this config file resides
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Candidate filenames for service account JSON
DEFAULT_SECRET_FILES = [
    os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"),
    #os.path.join(BASE_DIR, "client_secrets.json"),
    os.path.join(BASE_DIR, "credentials.json")
]
OAUTH_CREDENTIALS_FILE = os.path.join(BASE_DIR,os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE", "credentials.json")) 
# Pick the first existing path
SERVICE_ACCOUNT_FILE = None
for path in DEFAULT_SECRET_FILES:
    if path and os.path.isfile(path):
        SERVICE_ACCOUNT_FILE = path
        break

if not SERVICE_ACCOUNT_FILE:
    sys.exit(
        "Error: No valid service-account JSON found.\n"
        "Please set GOOGLE_SERVICE_ACCOUNT_FILE to the correct path,\n"
        "or place 'client_secrets.json' or 'credentials.json' in the same directory as this file."
    )
PARENT_FOLDER_ID = os.getenv("GOOGLE_DRIVE_PARENT_FOLDER_ID", "1pmMx_EmAVaFzoP79NCW8UOxvDZX6arYs")
SUBFOLDER_NAME = os.getenv("GOOGLE_DRIVE_SUBFOLDER_NAME", "test")

# Google Sheets configuration
LOG_SHEET_NAME = os.getenv("GOOGLE_SHEET_LOG_NAME", "logs")
INPUT_SHEET_NAME = os.getenv("GOOGLE_SHEET_INPUT_NAME", "FORM")
INPUT_SHEET_ID = os.getenv("GOOGLE_SHEET_INPUT_ID", "1H8uq7TgZC_d4imLA1jt9haut_Ff8RHzG69uFv0hXRUc")

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY","")
GEMINI_RATE_LIMIT_PER_MINUTE = int(os.getenv("GEMINI_RATE_LIMIT_PER_MINUTE", "60"))
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
GEMINI_BACKOFF_SECONDS = int(os.getenv("GEMINI_BACKOFF_SECONDS", "2"))
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
# Local paths for output
OUTPUT_BASE_DIR = os.getenv("OUTPUT_BASE_DIR", "output")
INITIAL_COLUMNS = ["Spec Section #", "Spec Section Name", "Mentioned Brands"]
FINAL_COLUMNS = [
    "Spec Section #",
    "Spec Section Name",
    "Mentioned Brands",
    "Newman Represented?",
    "Macaulay Represented?"
]

# Email configuration
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "ketanjp2019@gmail.com")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", ["scandles305@gmail.com"]),#,"juysal@uft.com"])
EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT", "RFP Processing Results")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "ketanhp79@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")