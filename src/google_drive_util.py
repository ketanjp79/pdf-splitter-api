
import os
import sys
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
import gspread
from src import config

class GoogleDriveUtility:
    """
    Utility for interacting with Google Drive and Sheets using OAuth.
    """
    def __init__(self):
        # Define scopes for Drive and Sheets API
        scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]

        # OAuth flow
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", scopes)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(config.OAUTH_CREDENTIALS_FILE, scopes)
            creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

        self.drive = build('drive', 'v3', credentials=creds)
        self.sheets = gspread.authorize(creds)
        self.parent_id = config.PARENT_FOLDER_ID
        self.subfolder_id = self.ensure_folder(config.SUBFOLDER_NAME, self.parent_id)

    def ensure_folder(self, folder_name, parent_id):
        query = (
            f"mimeType='application/vnd.google-apps.folder' and "
            f"name='{folder_name}' and '{parent_id}' in parents and trashed=false"
        )
        results = self.drive.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get("files", [])
        if folders:
            return folders[0]["id"]
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id]
        }
        folder = self.drive.files().create(body=file_metadata, fields="id").execute()
        return folder["id"]

    def get_or_create_pdf_root_folder(self, pdf_file_name):
        return self.get_or_create_named_folder(pdf_file_name, parent_id=self.subfolder_id)

    def get_or_create_pdf_subfolder(self, pdf_file_name, subfolder_name):
        pdf_root_id = self.get_or_create_pdf_root_folder(pdf_file_name)
        return self.get_or_create_named_folder(subfolder_name, parent_id=pdf_root_id)

    def get_or_create_pdf_folder(self, pdf_file_name):
        pdf_folder_name = config.sanitize_filename(pdf_file_name.rsplit('.', 1)[0])
        return self.ensure_folder(pdf_folder_name, self.subfolder_id)

    def get_or_create_subfolder(self, parent_id, subfolder_name):
        query = f"'{parent_id}' in parents and name='{subfolder_name}' and mimeType='application/vnd.google-apps.folder'"
        results = self.drive.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        if files:
            return files[0]['id']
        file_metadata = {
            'name': subfolder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = self.drive.files().create(body=file_metadata, fields='id').execute()
        return folder['id']

    def get_or_create_output_csv_folder(self, pdf_folder_id):
        return self.ensure_folder("output_csv", pdf_folder_id)

    def get_or_create_named_folder(self, folder_name, parent_id):
        query = (
            f"mimeType='application/vnd.google-apps.folder' and "
            f"name='{folder_name}' and "
            f"'{parent_id}' in parents and trashed=false"
        )
        results = self.drive.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])
        if files:
            return files[0]["id"]
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id]
        }
        folder = self.drive.files().create(body=file_metadata, fields="id").execute()
        return folder["id"]

    def get_or_create_output_csv_pdf_folder(self, pdf_file_name):
        output_csv_folder_id = self.get_or_create_named_folder('output_csv', parent_id=self.subfolder_id)
        pdf_csv_folder_id = self.get_or_create_named_folder(pdf_file_name, parent_id=output_csv_folder_id)
        return pdf_csv_folder_id

    def upload_file(self, file_path: str, folder_id: str = None) -> str:
        file_name = os.path.basename(file_path)
        if folder_id:
            query = (
                f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
            )
            results = self.drive.files().list(q=query, fields="files(id, webContentLink)").execute()
            files = results.get("files", [])
            if files:
                return files[0].get("webContentLink")
        file_metadata = {"name": file_name}
        if folder_id:
            file_metadata["parents"] = [folder_id]
        media = MediaFileUpload(file_path, resumable=True)
        uploaded = self.drive.files().create(
            body=file_metadata, media_body=media, fields="id, webContentLink"
        ).execute()
        return uploaded.get("webContentLink")

    def upload_section_csv(self, local_csv_path, pdf_file_name):
        pdf_folder_id = self.get_or_create_pdf_folder(pdf_file_name)
        output_csv_folder_id = self.get_or_create_output_csv_folder(pdf_folder_id)
        return self.upload_file(local_csv_path, folder_id=output_csv_folder_id)

    def upload_pdf(self, local_pdf_path, pdf_file_name):
        pdf_folder_id = self.get_or_create_pdf_folder(pdf_file_name)
        return self.upload_file(local_pdf_path, folder_id=pdf_folder_id)

    def download_file(self, file_id: str, dest_path: str) -> str:
        request = self.drive.files().get_media(fileId=file_id)
        fh = io.FileIO(dest_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.close()
        return dest_path

    def find_pdf_file_by_name(self, pdf_file_name):
        pdf_folder_id = self.get_or_create_pdf_folder(pdf_file_name)
        sanitized_pdf_name = os.path.basename(pdf_file_name)
        query = (
            f"name='{sanitized_pdf_name}' and "
            f"'{pdf_folder_id}' in parents and "
            "mimeType='application/pdf' and trashed=false"
        )
        response = self.drive.files().list(q=query, fields='files(id, name)').execute()
        files = response.get('files', [])
        if files:
            return files[0]['id']
        return None

    def log(self, sheet_name: str, row: list) -> None:
        sheet = self.sheets.open_by_key(config.INPUT_SHEET_ID)
        worksheet = sheet.get_worksheet(1)
        worksheet.append_row(row)
