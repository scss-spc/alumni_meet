from db.connection import execute_query, get_db_cursor
from typing import List, Dict, Any, Optional

def init_gallery_table():
    """Ensure gallery_photos table exists. Photos live on Google Drive; only file IDs are stored."""
    sql = """
        CREATE TABLE IF NOT EXISTS `gallery_photos` (
            `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
            `drive_file_id` VARCHAR(128) NOT NULL,
            `caption` VARCHAR(500) NULL,
            `album` VARCHAR(100) NULL,
            `is_published` BOOLEAN NOT NULL DEFAULT TRUE,
            `created_by` BIGINT NULL,
            `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT `uk_gallery_drive_file` UNIQUE (`drive_file_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    execute_query(sql, commit=True)

def add_photos(drive_file_ids: List[str], caption: Optional[str], album: Optional[str], created_by: Optional[int]) -> int:
    """Insert photos in one round trip, skipping Drive files that are already in the gallery."""
    if not drive_file_ids:
        return 0
    sql = """
        INSERT IGNORE INTO gallery_photos (drive_file_id, caption, album, created_by)
        VALUES (%s, %s, %s, %s)
    """
    with get_db_cursor(commit=True) as cursor:
        return cursor.executemany(sql, [(fid, caption, album, created_by) for fid in drive_file_ids]) or 0

def _build_filters(published_only: bool, album: Optional[str]):
    conditions = ["1=1"]
    params: List[Any] = []
    if published_only:
        conditions.append("is_published = TRUE")
    if album:
        conditions.append("album = %s")
        params.append(album)
    return " AND ".join(conditions), params

def get_photos(
    published_only: bool = True,
    album: Optional[str] = None,
    limit: int = 60,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Fetch gallery photos, newest first."""
    where_clause, params = _build_filters(published_only, album)
    sql = f"""
        SELECT id, drive_file_id, caption, album, is_published, created_at
        FROM gallery_photos
        WHERE {where_clause}
        ORDER BY created_at DESC, id DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    return execute_query(sql, tuple(params), fetch_all=True) or []

def count_photos(published_only: bool = True, album: Optional[str] = None) -> int:
    where_clause, params = _build_filters(published_only, album)
    sql = f"SELECT COUNT(*) AS total FROM gallery_photos WHERE {where_clause}"
    row = execute_query(sql, tuple(params), fetch_one=True)
    return int(row["total"]) if row else 0

def get_albums(published_only: bool = True) -> List[str]:
    """Distinct album names that have at least one photo."""
    where = "WHERE album IS NOT NULL AND album <> ''"
    if published_only:
        where += " AND is_published = TRUE"
    sql = f"SELECT DISTINCT album FROM gallery_photos {where} ORDER BY album ASC"
    return [r["album"] for r in (execute_query(sql, fetch_all=True) or [])]

def set_photo_published(photo_id: int, is_published: bool) -> int:
    sql = "UPDATE gallery_photos SET is_published = %s WHERE id = %s"
    return execute_query(sql, (is_published, photo_id), commit=True)

def update_photo_details(photo_id: int, caption: Optional[str], album: Optional[str]) -> int:
    sql = "UPDATE gallery_photos SET caption = %s, album = %s WHERE id = %s"
    return execute_query(sql, (caption, album, photo_id), commit=True)

def delete_photo(photo_id: int) -> int:
    sql = "DELETE FROM gallery_photos WHERE id = %s"
    return execute_query(sql, (photo_id,), commit=True)
