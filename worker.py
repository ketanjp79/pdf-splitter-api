from celery import Celery
from src.pdf_splitter import PDFSplitter
from src.google_drive_util import GoogleDriveUtility
import time, os, json
from src.utils import extract_drive_file_id
from src import config

celery = Celery(__name__, broker="redis://localhost:6379/0")

@celery.task
def split_pdf_from_drive_task(file_id: str, prefixes: str, task_id: str):
    file_id = extract_drive_file_id(file_id)
    drive = GoogleDriveUtility()
    file_metadata = drive.drive.files().get(fileId=file_id, fields="name").execute()
    pdf_file_name = file_metadata["name"]
    local_pdf = config.tmp_path(f"{file_id}.pdf")
    drive.download_file(file_id, local_pdf)
    splitter = PDFSplitter(local_pdf, output_base=config.OUTPUT_BASE_DIR, prefixes=prefixes)
    split_paths = splitter.split()
    links = [drive.upload_pdf(path, pdf_file_name) for path in split_paths]
    result_data = {"status": "success", "links": links}
    os.makedirs("results", exist_ok=True)
    with open(f"results/{task_id}.json", "w") as f:
        json.dump(result_data, f)
    return result_data