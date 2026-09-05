import re
from typing import Optional

def extract_google_drive_file_id(file_path_or_url: Optional[str]) -> Optional[str]:
    """
    Extract Google Drive File ID from either raw file ID, Google Drive URL, or stored path.
    """
    if not file_path_or_url:
        return None

    file_path_or_url = file_path_or_url.strip()

    # Pattern: https://drive.google.com/file/d/<FILE_ID>/...
    match = re.search(r"/file/d/([a-zA-Z0-9_-]+)", file_path_or_url)
    if match:
        return match.group(1)

    # Pattern: id=<FILE_ID>
    match = re.search(r"id=([a-zA-Z0-9_-]+)", file_path_or_url)
    if match:
        return match.group(1)

    # Pattern: open?id=<FILE_ID>
    match = re.search(r"open\?id=([a-zA-Z0-9_-]+)", file_path_or_url)
    if match:
        return match.group(1)

    # If it is already a pure alphanumeric file id
    if re.match(r"^[a-zA-Z0-9_-]{15,}$", file_path_or_url):
        return file_path_or_url

    return file_path_or_url

def get_drive_preview_url(file_path_or_url: Optional[str]) -> Optional[str]:
    """
    Generate Google Drive preview URL for authorized admin viewing.
    """
    file_id = extract_google_drive_file_id(file_path_or_url)
    if not file_id:
        return None

    if file_id.startswith("http"):
        return file_id

    return f"https://drive.google.com/file/d/{file_id}/view"

def get_drive_thumbnail_url(file_path_or_url: Optional[str]) -> Optional[str]:
    """
    Generate Google Drive thumbnail URL.
    """
    file_id = extract_google_drive_file_id(file_path_or_url)
    if not file_id:
        return None

    if file_id.startswith("http"):
        return file_id

    return f"https://drive.google.com/thumbnail?id={file_id}&sz=w600"
