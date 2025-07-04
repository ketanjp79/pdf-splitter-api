import re
import urllib.parse

def extract_drive_file_id(input_str: str) -> str:
    if "drive.google.com" in input_str:
        parsed = urllib.parse.urlparse(input_str)
        qs = urllib.parse.parse_qs(parsed.query)
        if "id" in qs:
            return qs["id"][0]
        m = re.search(r"/d/([a-zA-Z0-9_-]+)", input_str)
        if m:
            return m.group(1)
        m2 = re.search(r"id=([a-zA-Z0-9_-]+)", input_str)
        if m2:
            return m2.group(1)
        raise ValueError("Could not extract file ID from Google Drive URL.")
    return input_str