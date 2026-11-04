import re
import logging
from typing import List, Dict, Any, Optional, Tuple

from db.gallery import (
    init_gallery_table,
    add_photos,
    get_photos,
    count_photos,
    get_albums,
    get_album_previews,
    set_photo_published,
    update_photo_details,
    delete_photo
)
from services.drive_service import extract_google_drive_file_id, get_drive_thumbnail_url
from db.audit import log_audit_action

logger = logging.getLogger(__name__)

PHOTOS_PER_PAGE = 48
ALBUM_PREVIEW_SIZE = 8
_DRIVE_FILE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{20,}$")

def ensure_gallery_initialized():
    try:
        init_gallery_table()
    except Exception as e:
        logger.warning(f"Could not initialize gallery_photos table on startup: {e}")

def parse_drive_links(raw_text: str) -> Tuple[List[str], List[str]]:
    """
    Split pasted text (one link per line, commas also accepted) into Drive file IDs.
    Returns (unique_file_ids, rejected_lines). Folder links are rejected: each photo needs its own file link.
    """
    file_ids: List[str] = []
    rejected: List[str] = []
    for line in re.split(r"[\n,]+", raw_text or ""):
        line = line.strip()
        if not line:
            continue
        if "/folders/" in line:
            rejected.append(line)
            continue
        file_id = extract_google_drive_file_id(line)
        if file_id and _DRIVE_FILE_ID_RE.match(file_id):
            if file_id not in file_ids:
                file_ids.append(file_id)
        else:
            rejected.append(line)
    return file_ids, rejected

def _with_image_urls(photo: Dict[str, Any]) -> Dict[str, Any]:
    photo["thumb_url"] = get_drive_thumbnail_url(photo["drive_file_id"], width=480)
    photo["full_url"] = get_drive_thumbnail_url(photo["drive_file_id"], width=1600)
    return photo

def get_public_gallery(album: Optional[str] = None, page: int = 1) -> Dict[str, Any]:
    """
    Public gallery data.
    - album given: that album's photos, paginated.
    - no album: one section per album (newest ALBUM_PREVIEW_SIZE photos each, linking to the full album),
      followed by paginated photos that have no album.
    """
    page = max(page, 1)
    groups: List[Dict[str, Any]] = []
    try:
        if album:
            total = count_photos(published_only=True, album=album)
            photos = get_photos(published_only=True, album=album, limit=PHOTOS_PER_PAGE, offset=(page - 1) * PHOTOS_PER_PAGE)
        else:
            for row in get_album_previews(ALBUM_PREVIEW_SIZE):
                if not groups or groups[-1]["name"] != row["album"]:
                    groups.append({"name": row["album"], "total": int(row["album_total"]), "photos": []})
                groups[-1]["photos"].append(_with_image_urls(row))
            total = count_photos(published_only=True, ungrouped=True)
            photos = get_photos(published_only=True, ungrouped=True, limit=PHOTOS_PER_PAGE, offset=(page - 1) * PHOTOS_PER_PAGE)
        albums = get_albums(published_only=True)
    except Exception as e:
        logger.error(f"Failed to load gallery: {e}")
        total, photos, albums, groups = 0, [], [], []

    return {
        "groups": groups,
        "photos": [_with_image_urls(p) for p in photos],
        "albums": albums,
        "selected_album": album,
        "page": page,
        "total": total,
        "has_next": page * PHOTOS_PER_PAGE < total,
        "has_prev": page > 1,
    }

def get_gallery_preview(limit: int = 6) -> List[Dict[str, Any]]:
    """Latest published photos for the homepage teaser. Never raises, so the homepage still renders."""
    try:
        return [_with_image_urls(p) for p in get_photos(published_only=True, limit=limit)]
    except Exception as e:
        logger.error(f"Failed to load gallery preview: {e}")
        return []

def get_admin_gallery() -> Dict[str, Any]:
    photos = get_photos(published_only=False, limit=500)
    return {
        "photos": [_with_image_urls(p) for p in photos],
        "albums": get_albums(published_only=False),
    }

def add_gallery_photos(raw_links: str, caption: Optional[str], album: Optional[str], user_id: Optional[int]) -> Dict[str, Any]:
    file_ids, rejected = parse_drive_links(raw_links)
    added = add_photos(file_ids, caption or None, album or None, user_id) if file_ids else 0
    if added:
        log_audit_action(
            user_id=user_id,
            action="add_gallery_photos",
            entity_type="gallery_photo",
            new_value=f"{added} photo(s) added to album '{album or '—'}'"
        )
    return {
        "added": added,
        "duplicates": len(file_ids) - added,
        "rejected": rejected,
    }

def toggle_photo_published(photo_id: int, is_published: bool, user_id: Optional[int]):
    set_photo_published(photo_id, is_published)
    log_audit_action(
        user_id=user_id,
        action="publish_gallery_photo" if is_published else "hide_gallery_photo",
        entity_type="gallery_photo",
        entity_id=photo_id
    )

def edit_photo(photo_id: int, caption: Optional[str], album: Optional[str], user_id: Optional[int]):
    update_photo_details(photo_id, caption or None, album or None)
    log_audit_action(
        user_id=user_id,
        action="edit_gallery_photo",
        entity_type="gallery_photo",
        entity_id=photo_id,
        new_value=f"caption={caption!r}, album={album!r}"
    )

def remove_photo(photo_id: int, user_id: Optional[int]):
    delete_photo(photo_id)
    log_audit_action(
        user_id=user_id,
        action="delete_gallery_photo",
        entity_type="gallery_photo",
        entity_id=photo_id
    )
