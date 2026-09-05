import re
import csv
import io
import logging
from typing import List, Dict, Any, Optional, Tuple
import requests

logger = logging.getLogger(__name__)

# Standard normalization aliases for Google Form responses
COLUMN_ALIASES = {
    "full_name": [
        "full name", "name", "alumnus name", "alumni name", "your name",
        "name of alumnus", "participant name", "candidate name"
    ],
    "email": [
        "email", "email address", "e-mail", "e-mail address", "mail",
        "username", "email id", "contact email"
    ],
    "phone": [
        "phone", "phone number", "contact", "contact number", "mobile",
        "mobile number", "whatsapp", "whatsapp number", "telephone", "cell"
    ],
    "graduation_year": [
        "graduation year", "year of passing", "passing year", "batch",
        "passout year", "batch year", "year of graduation", "year"
    ],
    "course": [
        "course", "program", "programme", "degree", "branch",
        "course / program", "degree / program", "department"
    ],
    "organization": [
        "organization", "organisation", "current organization", "current organisation",
        "company", "workplace", "employer", "institution", "current company",
        "company / organization", "present organization"
    ],
    "designation": [
        "designation", "job title", "role", "current designation", "title",
        "position", "current role", "present designation"
    ],
    "current_location": [
        "current location", "location", "city", "current city",
        "city of residence", "residence city", "country", "present location"
    ],
    "attending": [
        "will you attend", "will you be attending", "attending", "are you attending",
        "joining", "participation", "rsvp", "attendance", "attending the meet?",
        "will you be attending the alumni meet?"
    ],
    "guest_count": [
        "guest count", "number of guests", "guests", "accompanying persons",
        "family members", "additional guests", "plus ones", "accompanying guest count",
        "how many guests are accompanying you?"
    ],
    "dietary_preferences": [
        "dietary preferences", "dietary preference", "food preference", "meal preference",
        "diet", "food", "food choice", "vegetarian / non-vegetarian"
    ],
    "suggestions": [
        "suggestions", "suggestions / notes", "feedback", "messages", "ideas",
        "comments", "notes", "any suggestions", "message for batchmates",
        "suggestions for the event"
    ],
    "amount": [
        "contribution amount", "amount", "donation", "contribution", "registration fee",
        "fees", "amount paid", "paid amount", "contribution (inr)", "amount (₹)"
    ],
    "transaction_reference": [
        "transaction reference", "transaction id", "utr", "utr number", "reference id",
        "ref no", "txn id", "transaction no", "payment reference", "upi ref",
        "transaction / utr reference"
    ],
    "payment_screenshot_path": [
        "payment screenshot", "screenshot", "payment proof", "receipt", "drive link",
        "upload receipt", "upload payment screenshot", "payment receipt upload",
        "attach payment screenshot"
    ],
    "recognition_type": [
        "recognition type", "recognition preference", "public recognition",
        "display preference", "recognition", "donor recognition preference",
        "how would you like to be recognized?"
    ]
}

def clean_header_text(header: str) -> str:
    """Normalize raw header string for fuzzy matching."""
    if not header:
        return ""
    text = header.strip().lower()
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def detect_column_mapping(headers: List[str]) -> Dict[str, str]:
    """
    Map raw sheet column headers to canonical database field names.
    Returns dict: canonical_name -> raw_header
    """
    mapping: Dict[str, str] = {}
    cleaned_headers = [(h, clean_header_text(h)) for h in headers if h]

    for canonical, aliases in COLUMN_ALIASES.items():
        # First: exact match with alias
        for raw_h, clean_h in cleaned_headers:
            if clean_h in aliases:
                mapping[canonical] = raw_h
                break

        # Second: substring or word-boundary match if not yet mapped
        if canonical not in mapping:
            for raw_h, clean_h in cleaned_headers:
                for alias in aliases:
                    if alias in clean_h or clean_h in alias:
                        mapping[canonical] = raw_h
                        break
                if canonical in mapping:
                    break

    return mapping

def parse_year(val: Any) -> Optional[int]:
    """Parse graduation year from diverse formats (e.g., '2018', 'Batch of 2018', 2018.0)."""
    if val is None or val == "":
        return None
    val_str = str(val).strip()
    match = re.search(r"\b(19\d\d|20\d\d)\b", val_str)
    if match:
        return int(match.group(1))
    return None

def parse_boolean_attending(val: Any) -> bool:
    """Parse attendance status from form response."""
    if val is None:
        return True
    val_str = str(val).strip().lower()
    if val_str in ("yes", "y", "true", "1", "attending", "confirm", "confirmed", "definitely", "joining"):
        return True
    if val_str in ("no", "n", "false", "0", "not attending", "cannot attend", "declined", "can't make it"):
        return False
    return True

def parse_guest_count(val: Any) -> int:
    """Parse number of guests accompanying alumnus."""
    if val is None or val == "":
        return 0
    val_str = str(val).strip()
    match = re.search(r"\b(\d+)\b", val_str)
    if match:
        try:
            return max(0, int(match.group(1)))
        except ValueError:
            return 0
    return 0

def parse_amount(val: Any) -> float:
    """Parse financial amount (stripping currency symbols, commas)."""
    if val is None or val == "":
        return 0.0
    val_str = str(val).replace(",", "").replace("₹", "").replace("$", "").strip()
    match = re.search(r"[-+]?\d*\.?\d+", val_str)
    if match:
        try:
            return max(0.0, float(match.group(0)))
        except ValueError:
            return 0.0
    return 0.0

def parse_recognition_preference(val: Any) -> str:
    """Normalize public recognition preference enum using the 3-tier privacy engine."""
    from services.privacy_service import classify_recognition_mode
    return classify_recognition_mode(val)

class GoogleSheetsConnector:
    """Connector for fetching alumni response data from Google Sheets."""

    def __init__(
        self,
        sheet_id: Optional[str] = None,
        sheet_name: str = "Form Responses 1",
        csv_url: Optional[str] = None,
        service_account_file: Optional[str] = None,
        service_account_json: Optional[str] = None
    ):
        self.sheet_id = (sheet_id or "").strip()
        self.sheet_name = (sheet_name or "Form Responses 1").strip()
        self.csv_url = (csv_url or "").strip()
        self.service_account_file = (service_account_file or "").strip()
        self.service_account_json = (service_account_json or "").strip()

    def get_public_csv_url(self) -> str:
        """Construct public CSV export URL from Google Sheet ID."""
        if self.csv_url:
            return self.csv_url
        if not self.sheet_id:
            raise ValueError("Neither GOOGLE_SHEET_ID nor GOOGLE_SHEET_CSV_URL is configured.")

        # Extract Sheet ID if user provided full URL
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", self.sheet_id)
        sheet_id = match.group(1) if match else self.sheet_id

        # Use gviz endpoint or export format=csv
        if self.sheet_name:
            import urllib.parse
            encoded_name = urllib.parse.quote(self.sheet_name)
            return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"

    def fetch_via_service_account(self) -> List[Dict[str, Any]]:
        """Fetch sheet rows using Google Service Account credentials via Google Sheets API v4."""
        try:
            from google.oauth2 import service_account
            import google.auth.transport.requests

            scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
            if self.service_account_file:
                creds = service_account.Credentials.from_service_account_file(
                    self.service_account_file, scopes=scopes
                )
            elif self.service_account_json:
                import json
                info = json.loads(self.service_account_json)
                creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)
            else:
                raise ValueError("No Service Account credentials provided.")

            # Refresh token to get bearer access token
            request_obj = google.auth.transport.requests.Request()
            creds.refresh(request_obj)
            token = creds.token

            sheet_id = self.sheet_id
            match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", sheet_id)
            if match:
                sheet_id = match.group(1)

            range_name = f"'{self.sheet_name}'" if self.sheet_name else "A:ZZ"
            import urllib.parse
            encoded_range = urllib.parse.quote(range_name)
            api_url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{encoded_range}"

            resp = requests.get(
                api_url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            values = data.get("values", [])

            if not values:
                return []

            headers = [str(h) for h in values[0]]
            rows = []
            for row in values[1:]:
                # Pad row to match header length
                padded = row + [""] * (len(headers) - len(row))
                row_dict = {headers[i]: padded[i] for i in range(len(headers))}
                rows.append(row_dict)

            return rows

        except Exception as e:
            logger.error(f"Failed to fetch via Google Service Account: {e}")
            raise

    def fetch_via_csv_url(self) -> List[Dict[str, Any]]:
        """Fetch sheet rows via public/shared Google Sheet CSV export URL."""
        # Try primary URL first, then fallback to gid=0 if named sheet export fails
        urls_to_try = [self.get_public_csv_url()]
        if self.sheet_id:
            match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", self.sheet_id)
            sheet_id = match.group(1) if match else self.sheet_id
            gid0_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
            if gid0_url not in urls_to_try:
                urls_to_try.append(gid0_url)

        last_error = None
        for url in urls_to_try:
            logger.info(f"Fetching Google Sheet CSV from URL: {url}")
            try:
                response = requests.get(
                    url,
                    timeout=20,
                    headers={"User-Agent": "SCSS-JNU-AlumniMeet-Sync/1.0"}
                )

                if response.status_code in (401, 403):
                    raise PermissionError(
                        "Google Sheet access denied (401/403 Unauthorized). "
                        "Please open your Google Sheet, click 'Share' (top right), and set General Access to "
                        "'Anyone with the link' (Viewer). Alternatively, configure a Google Service Account."
                    )

                response.raise_for_status()

                # Check if response is an HTML login page (indicates private sheet)
                content_type = response.headers.get("Content-Type", "").lower()
                if "text/html" in content_type and ("ServiceLogin" in response.text or "accounts.google.com" in response.text):
                    raise PermissionError(
                        "Google Sheet is private and requires login. "
                        "Please click 'Share' in Google Sheets and set General Access to 'Anyone with the link can view'."
                    )

                csv_text = response.content.decode("utf-8-sig", errors="replace")
                reader = csv.DictReader(io.StringIO(csv_text))
                rows = [row for row in reader]
                return rows

            except PermissionError:
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to fetch CSV from {url}: {e}")

        if last_error:
            raise last_error
        return []

    def fetch_raw_data(self) -> List[Dict[str, Any]]:
        """Fetch raw sheet data using configured credentials or CSV fallback."""
        if self.service_account_file or self.service_account_json:
            try:
                return self.fetch_via_service_account()
            except Exception as e:
                logger.warning(f"Service account fetch failed ({e}); falling back to CSV export URL.")

        return self.fetch_via_csv_url()

    def fetch_and_normalize(self) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Fetch sheet data and normalize into structured records ready for database upsert.
        Returns (records_list, detected_header_mapping).
        """
        raw_rows = self.fetch_raw_data()
        if not raw_rows:
            return [], {}

        headers = list(raw_rows[0].keys())
        col_map = detect_column_mapping(headers)
        logger.info(f"Detected Google Sheet Column Mappings: {col_map}")

        normalized_records: List[Dict[str, Any]] = []

        for idx, row in enumerate(raw_rows, start=2): # 1-indexed row number, skipping header
            def get_val(canonical_key: str) -> Optional[str]:
                h = col_map.get(canonical_key)
                if h and h in row:
                    val = row[h]
                    return str(val).strip() if val is not None else None
                return None

            email = get_val("email")
            full_name = get_val("full_name")

            # Email and name are minimum required to identify alumnus
            if not email or not full_name:
                logger.debug(f"Row {idx} missing required name or email; skipping.")
                continue

            email_clean = email.strip().lower()
            if "@" not in email_clean or "." not in email_clean:
                logger.warning(f"Row {idx} has invalid email format '{email}'; skipping.")
                continue

            guest_count = parse_guest_count(get_val("guest_count"))
            is_attending = parse_boolean_attending(get_val("attending"))
            total_attendees = (1 + guest_count) if is_attending else 0

            record = {
                "row_number": idx,
                # Alumni metadata
                "full_name": full_name.strip(),
                "email": email_clean,
                "phone": get_val("phone"),
                "graduation_year": parse_year(get_val("graduation_year")),
                "course": get_val("course"),
                "organization": get_val("organization"),
                "designation": get_val("designation"),
                "current_location": get_val("current_location"),
                
                # Meet Attendance
                "attending": is_attending,
                "guest_count": guest_count,
                "total_attendees": total_attendees,
                "dietary_preferences": get_val("dietary_preferences"),
                "suggestions": get_val("suggestions"),

                # Contribution / Payment
                "amount": parse_amount(get_val("amount")),
                "transaction_reference": get_val("transaction_reference"),
                "payment_screenshot_path": get_val("payment_screenshot_path"),

                # Recognition Preference
                "recognition_type": parse_recognition_preference(get_val("recognition_type"))
            }

            normalized_records.append(record)

        return normalized_records, col_map
