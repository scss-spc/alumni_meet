import logging
from typing import List, Dict, Any, Optional
from db.connection import execute_query, get_db_cursor

logger = logging.getLogger(__name__)

DEFAULT_SECTIONS = [
    # INDEX PAGE
    {
        "page": "index",
        "section_key": "hero_eyebrow",
        "title": "Hero Eyebrow Text",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "School of Computer & Systems Sciences · JNU"
    },
    {
        "page": "index",
        "section_key": "hero_title",
        "title": "Hero Main Heading",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "Alumni Meet 2026"
    },
    {
        "page": "index",
        "section_key": "hero_lead",
        "title": "Hero Subheading / Lead Text",
        "category": "Hero Section",
        "content_type": "textarea",
        "default_value": "Returning to the place where many of our journeys began. A gathering of alumni, distinguished faculty, scholars, and friends who have been part of the enduring SC&SS story."
    },
    {
        "page": "index",
        "section_key": "hero_badge",
        "title": "Hero Card Badge",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "SC&SS · JNU Gathering"
    },
    {
        "page": "index",
        "section_key": "hero_card_title",
        "title": "Hero Card Title",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "An Enduring Academic Community"
    },
    {
        "page": "index",
        "section_key": "hero_card_text",
        "title": "Hero Card Description",
        "category": "Hero Section",
        "content_type": "textarea",
        "default_value": "From pioneering researchers in computing systems to leaders shaping modern technology and academia globally, the SC&SS fraternity spans generations across the world."
    },
    {
        "page": "index",
        "section_key": "hero_btn_primary",
        "title": "Primary Button Text",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "Register & Contribute via Google Form"
    },
    {
        "page": "index",
        "section_key": "hero_btn_secondary",
        "title": "Secondary Button Text",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "View Meet Schedule"
    },
    {
        "page": "index",
        "section_key": "s1_label",
        "title": "Section 01 Tag Label",
        "category": "Section 01 - About the Meet",
        "content_type": "text",
        "default_value": "About the Meet"
    },
    {
        "page": "index",
        "section_key": "s1_title",
        "title": "Section 01 Heading",
        "category": "Section 01 - About the Meet",
        "content_type": "text",
        "default_value": "Years After Leaving JNU, the Connection Endures"
    },
    {
        "page": "index",
        "section_key": "s1_lead",
        "title": "Section 01 Lead Paragraph",
        "category": "Section 01 - About the Meet",
        "content_type": "textarea",
        "default_value": "The SC&SS Alumni Meet 2026 is an opportunity to walk down familiar campus pathways, catch up with batchmates, meet current scholars, and strengthen the alumni network."
    },
    {
        "page": "index",
        "section_key": "s1_body",
        "title": "Section 01 Secondary Paragraph",
        "category": "Section 01 - About the Meet",
        "content_type": "textarea",
        "default_value": "Whether you graduated in the early batches of MCA and M.Tech or recently completed your Ph.D., your presence enriches the school's legacy."
    },
    {
        "page": "index",
        "section_key": "s1_highlights_title",
        "title": "Section 01 Highlights Card Title",
        "category": "Section 01 - About the Meet",
        "content_type": "text",
        "default_value": "Event Highlights"
    },
    {
        "page": "index",
        "section_key": "s2_label",
        "title": "Section 02 Tag Label",
        "category": "Section 02 - Institutional Heritage",
        "content_type": "text",
        "default_value": "The School"
    },
    {
        "page": "index",
        "section_key": "s2_title",
        "title": "Section 02 Heading",
        "category": "Section 02 - Institutional Heritage",
        "content_type": "text",
        "default_value": "A Tradition of Scientific Inquiry & Systems Leadership"
    },
    {
        "page": "index",
        "section_key": "s2_lead",
        "title": "Section 02 Lead Text",
        "category": "Section 02 - Institutional Heritage",
        "content_type": "textarea",
        "default_value": "Established as one of the premier computer and systems science schools in India, SC&SS JNU has continuously fostered rigorous academic inquiry and technological innovation."
    },
    {
        "page": "index",
        "section_key": "s2_p1_title",
        "title": "Pillar 01 Title",
        "category": "Section 02 - Institutional Heritage",
        "content_type": "text",
        "default_value": "Academic Rigor"
    },
    {
        "page": "index",
        "section_key": "s2_p1_text",
        "title": "Pillar 01 Description",
        "category": "Section 02 - Institutional Heritage",
        "content_type": "textarea",
        "default_value": "Rooted in mathematical foundations, theoretical computer science, databases, and distributed systems, producing thinkers who excel worldwide."
    },
    {
        "page": "index",
        "section_key": "s2_p2_title",
        "title": "Pillar 02 Title",
        "category": "Section 02 - Institutional Heritage",
        "content_type": "text",
        "default_value": "Vibrant Alumni"
    },
    {
        "page": "index",
        "section_key": "s2_p2_text",
        "title": "Pillar 02 Description",
        "category": "Section 02 - Institutional Heritage",
        "content_type": "textarea",
        "default_value": "Graduates leading technology organizations, research laboratories, universities, government bodies, and innovative startups globally."
    },
    {
        "page": "index",
        "section_key": "s2_p3_title",
        "title": "Pillar 03 Title",
        "category": "Section 02 - Institutional Heritage",
        "content_type": "text",
        "default_value": "Future Vision"
    },
    {
        "page": "index",
        "section_key": "s2_p3_text",
        "title": "Pillar 03 Description",
        "category": "Section 02 - Institutional Heritage",
        "content_type": "textarea",
        "default_value": "Advancing research in artificial intelligence, cyber-physical systems, quantum computing, and data sciences while nurturing the next generation."
    },
    {
        "page": "index",
        "section_key": "quote_text",
        "title": "Closing Quote",
        "category": "Closing Quote",
        "content_type": "textarea",
        "default_value": "\"The School remains a part of the journeys that began here.\""
    },
    {
        "page": "index",
        "section_key": "quote_sub",
        "title": "Closing Quote Subtitle",
        "category": "Closing Quote",
        "content_type": "text",
        "default_value": "SC&SS · Jawaharlal Nehru University"
    },

    # MEET PAGE
    {
        "page": "meet",
        "section_key": "hero_eyebrow",
        "title": "Hero Eyebrow Text",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "School of Computer & Systems Sciences · JNU"
    },
    {
        "page": "meet",
        "section_key": "hero_title",
        "title": "Hero Main Heading",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "Alumni Meet 2026 Details & Schedule"
    },
    {
        "page": "meet",
        "section_key": "hero_lead",
        "title": "Hero Subheading / Lead Text",
        "category": "Hero Section",
        "content_type": "textarea",
        "default_value": "Key information regarding schedule, campus access, venue arrangements, faculty felicitation, and alumni participation."
    },
    {
        "page": "meet",
        "section_key": "hero_btn_primary",
        "title": "Primary Button Text",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "RSVP & Register via Google Form"
    },
    {
        "page": "meet",
        "section_key": "hero_btn_secondary",
        "title": "Secondary Button Text",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "View Contribution Tracker"
    },
    {
        "page": "meet",
        "section_key": "hero_badge",
        "title": "Hero Card Badge",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "SC&SS · Event Summary"
    },
    {
        "page": "meet",
        "section_key": "hero_card_title",
        "title": "Hero Card Title",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "Gathering at JNU Campus"
    },
    {
        "page": "meet",
        "section_key": "hero_card_text",
        "title": "Hero Card Description",
        "category": "Hero Section",
        "content_type": "textarea",
        "default_value": "Bringing together alumni across MCA, M.Tech, and Ph.D. batches along with revered faculty and current scholars for a day of celebration, memories, and future collaboration."
    },
    {
        "page": "meet",
        "section_key": "s1_label",
        "title": "Section 01 Tag Label",
        "category": "Section 01 - Program & Venue",
        "content_type": "text",
        "default_value": "Program & Venue"
    },
    {
        "page": "meet",
        "section_key": "s1_title",
        "title": "Section 01 Heading",
        "category": "Section 01 - Program & Venue",
        "content_type": "text",
        "default_value": "Event Logistics & Campus Access"
    },
    {
        "page": "meet",
        "section_key": "s2_label",
        "title": "Section 02 Tag Label",
        "category": "Section 02 - Schedule",
        "content_type": "text",
        "default_value": "Schedule"
    },
    {
        "page": "meet",
        "section_key": "s2_title",
        "title": "Section 02 Heading",
        "category": "Section 02 - Schedule",
        "content_type": "text",
        "default_value": "Tentative Program & Activities"
    },
    {
        "page": "meet",
        "section_key": "s2_lead",
        "title": "Section 02 Lead Text",
        "category": "Section 02 - Schedule",
        "content_type": "textarea",
        "default_value": "A day filled with reconnecting, honoring revered faculty, interactive sessions, and memory walks across campus pathways:"
    },
    {
        "page": "meet",
        "section_key": "s3_label",
        "title": "Section 03 Tag Label",
        "category": "Section 03 - Highlights",
        "content_type": "text",
        "default_value": "Highlights"
    },
    {
        "page": "meet",
        "section_key": "s3_title",
        "title": "Section 03 Heading",
        "category": "Section 03 - Highlights",
        "content_type": "text",
        "default_value": "What to Expect at the Meet"
    },
    {
        "page": "meet",
        "section_key": "s4_label",
        "title": "Section 04 Tag Label",
        "category": "Section 04 - Attendance Banner",
        "content_type": "text",
        "default_value": "Attendance"
    },
    {
        "page": "meet",
        "section_key": "s4_title",
        "title": "Section 04 Heading",
        "category": "Section 04 - Attendance Banner",
        "content_type": "text",
        "default_value": "Confirm Your Attendance & RSVP"
    },
    {
        "page": "meet",
        "section_key": "s4_text",
        "title": "Section 04 Banner Description",
        "category": "Section 04 - Attendance Banner",
        "content_type": "textarea",
        "default_value": "Please submit your RSVP, guest counts, dietary preferences, and optional contribution via our official Google Form."
    },
    {
        "page": "meet",
        "section_key": "quote_text",
        "title": "Closing Quote",
        "category": "Closing Quote",
        "content_type": "textarea",
        "default_value": "\"Reconnecting generations of scholars who share a common heritage.\""
    },


    # CONTRIBUTE PAGE
    {
        "page": "contribute",
        "section_key": "hero_eyebrow",
        "title": "Hero Eyebrow Text",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "SC&SS JNU Alumni Meet 2026 · Financial Transparency"
    },
    {
        "page": "contribute",
        "section_key": "hero_title",
        "title": "Hero Main Heading",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "Contribution Tracker & Honor Roll"
    },
    {
        "page": "contribute",
        "section_key": "hero_lead",
        "title": "Hero Subheading / Lead Text",
        "category": "Hero Section",
        "content_type": "textarea",
        "default_value": "Every contribution fuels our collective gathering, faculty felicitations, student subsidies, and legacy archives. Track our progress in real-time with full transparency."
    },
    {
        "page": "contribute",
        "section_key": "s1_label",
        "title": "Section 01 Tag Label",
        "category": "Section 01 - Honor Roll",
        "content_type": "text",
        "default_value": "Honor Roll"
    },
    {
        "page": "contribute",
        "section_key": "s1_title",
        "title": "Section 01 Heading",
        "category": "Section 01 - Honor Roll",
        "content_type": "text",
        "default_value": "SC&SS Alumni Supporter Roll"
    },
    {
        "page": "contribute",
        "section_key": "s1_lead",
        "title": "Section 01 Lead Text",
        "category": "Section 01 - Honor Roll",
        "content_type": "textarea",
        "default_value": "Recognizing generous alumni supporters and contributors participating in the SC&SS Alumni Meet 2026."
    },
    {
        "page": "contribute",
        "section_key": "s2_label",
        "title": "Section 02 Tag Label",
        "category": "Section 02 - Fund Utilization",
        "content_type": "text",
        "default_value": "Fund Utilization"
    },
    {
        "page": "contribute",
        "section_key": "s2_title",
        "title": "Section 02 Heading",
        "category": "Section 02 - Fund Utilization",
        "content_type": "text",
        "default_value": "Transparent Allocation & Purpose"
    },
    {
        "page": "contribute",
        "section_key": "s2_lead",
        "title": "Section 02 Lead Text",
        "category": "Section 02 - Fund Utilization",
        "content_type": "textarea",
        "default_value": "Every contribution directly powers the event experience, faculty recognition, and student volunteer facilitation."
    },
    {
        "page": "contribute",
        "section_key": "s3_label",
        "title": "Section 03 Tag Label",
        "category": "Section 03 - Support CTA",
        "content_type": "text",
        "default_value": "Support the Meet"
    },
    {
        "page": "contribute",
        "section_key": "s3_title",
        "title": "Section 03 Heading",
        "category": "Section 03 - Support CTA",
        "content_type": "text",
        "default_value": "Support the SC&SS Alumni Meet 2026"
    },
    {
        "page": "contribute",
        "section_key": "s3_text",
        "title": "Section 03 Banner Description",
        "category": "Section 03 - Support CTA",
        "content_type": "textarea",
        "default_value": "Make your voluntary contribution and participation submission in the official intake form."
    },
    # SHARED EVENT FACTS (used by every page; edit once)
    {
        "page": "event",
        "section_key": "date",
        "title": "Event Date",
        "category": "Event Details",
        "content_type": "text",
        "default_value": "Saturday, 5 December 2026"
    },
    {
        "page": "event",
        "section_key": "timing",
        "title": "Event Timing",
        "category": "Event Details",
        "content_type": "text",
        "default_value": "09:30 AM – 05:00 PM IST"
    },
    {
        "page": "event",
        "section_key": "venue",
        "title": "Venue",
        "category": "Event Details",
        "content_type": "text",
        "default_value": "Convention Centre / SC&SS Auditorium, Jawaharlal Nehru University, New Delhi"
    },
    {
        "page": "event",
        "section_key": "status",
        "title": "Registration Status",
        "category": "Event Details",
        "content_type": "text",
        "default_value": "Registration Open"
    },
    {
        "page": "index",
        "section_key": "s3_label",
        "title": "Gallery Label",
        "category": "Section 03 - Gallery",
        "content_type": "text",
        "default_value": "Gallery"
    },
    {
        "page": "index",
        "section_key": "s3_title",
        "title": "Gallery Title",
        "category": "Section 03 - Gallery",
        "content_type": "text",
        "default_value": "Moments from the SC&SS Community"
    },
    {
        "page": "gallery",
        "section_key": "hero_title",
        "title": "Gallery Title",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "Alumni Gallery"
    },
    {
        "page": "gallery",
        "section_key": "hero_lead",
        "title": "Gallery Intro",
        "category": "Hero Section",
        "content_type": "text",
        "default_value": "Photographs from alumni meets, batch reunions, and life at SC&SS over the years."
    }
]

_DEFAULT_KEYS = {(sec["page"], sec["section_key"]) for sec in DEFAULT_SECTIONS}

# Retired per-page duplicates -> shared key that replaced them. Used once to preserve admin edits.
LEGACY_SECTION_MOVES = {
    ("event", "date"): ("index", "hero_date"),
    ("event", "venue"): ("index", "hero_venue"),
    ("event", "status"): ("index", "hero_status"),
    ("event", "timing"): ("meet", "hero_timing"),
}

def init_site_sections_table():
    """Ensure site_sections table exists and initial seed rows are inserted."""
    create_sql = """
        CREATE TABLE IF NOT EXISTS `site_sections` (
            `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
            `page` VARCHAR(50) NOT NULL,
            `section_key` VARCHAR(100) NOT NULL,
            `title` VARCHAR(255) NOT NULL,
            `category` VARCHAR(100) NOT NULL DEFAULT 'General',
            `content_type` VARCHAR(30) NOT NULL DEFAULT 'text',
            `content_value` LONGTEXT NULL,
            `default_value` LONGTEXT NULL,
            `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            `updated_by` BIGINT NULL,
            CONSTRAINT `uk_page_section` UNIQUE (`page`, `section_key`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    insert_sql = """
        INSERT INTO site_sections (
            page, section_key, title, category, content_type, default_value
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            category = VALUES(category),
            content_type = VALUES(content_type),
            default_value = VALUES(default_value)
    """
    rows = [
        (sec["page"], sec["section_key"], sec["title"], sec["category"], sec["content_type"], sec["default_value"])
        for sec in DEFAULT_SECTIONS
    ]
    # Carry admin edits from retired per-page keys into the shared event.* keys (only if not already set).
    carry_over_sql = """
        UPDATE site_sections dst
        JOIN site_sections src ON src.page = %s AND src.section_key = %s
        SET dst.content_value = src.content_value
        WHERE dst.page = %s AND dst.section_key = %s
          AND (dst.content_value IS NULL OR dst.content_value = '')
          AND src.content_value IS NOT NULL AND src.content_value <> ''
    """
    # Single connection + batched multi-row upsert: one TLS handshake instead of one per section.
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(create_sql)
        cursor.executemany(insert_sql, rows)
        for (dst_page, dst_key), (src_page, src_key) in LEGACY_SECTION_MOVES.items():
            cursor.execute(carry_over_sql, (src_page, src_key, dst_page, dst_key))

def prune_retired_sections() -> int:
    """Delete site_sections rows whose (page, section_key) is no longer in DEFAULT_SECTIONS."""
    rows = execute_query("SELECT id, page, section_key FROM site_sections", fetch_all=True) or []
    retired_ids = [r["id"] for r in rows if (r["page"], r["section_key"]) not in _DEFAULT_KEYS]
    if not retired_ids:
        return 0
    placeholders = ", ".join(["%s"] * len(retired_ids))
    return execute_query(f"DELETE FROM site_sections WHERE id IN ({placeholders})", tuple(retired_ids), commit=True)

def get_all_sections(page: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all site section records, optionally filtered by page."""
    if page and page.strip() and page.lower() != "all":
        sql = """
            SELECT id, page, section_key, title, category, content_type,
                   content_value, default_value, updated_at, updated_by
            FROM site_sections
            WHERE page = %s
            ORDER BY page ASC, category ASC, id ASC
        """
        rows = execute_query(sql, (page.strip().lower(),), fetch_all=True) or []
    else:
        sql = """
            SELECT id, page, section_key, title, category, content_type,
                   content_value, default_value, updated_at, updated_by
            FROM site_sections
            ORDER BY page ASC, category ASC, id ASC
        """
        rows = execute_query(sql, fetch_all=True) or []
    # Retired keys may linger until prune_retired_sections() runs; never surface them.
    return [r for r in rows if (r["page"], r["section_key"]) in _DEFAULT_KEYS]

def get_sections_dict() -> Dict[str, str]:
    """
    Returns a dictionary mapping 'page.section_key' -> current text value.
    If content_value is non-empty, uses content_value; otherwise falls back to default_value.
    """
    sections = get_all_sections()
    res = {}
    for s in sections:
        key = f"{s['page']}.{s['section_key']}"
        val = s.get("content_value")
        if val is None or val.strip() == "":
            val = s.get("default_value") or ""
        res[key] = val
    return res

def get_section_by_id(section_id: int) -> Optional[Dict[str, Any]]:
    """Fetch section details by ID."""
    sql = "SELECT id, page, section_key, title, category, content_type, content_value, default_value FROM site_sections WHERE id = %s"
    return execute_query(sql, (section_id,), fetch_one=True)

def update_section(section_id: int, content_value: Optional[str], updated_by: Optional[int] = None) -> bool:
    """Update section content_value by ID."""
    sql = """
        UPDATE site_sections
        SET content_value = %s,
            updated_by = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    execute_query(sql, (content_value if content_value is not None else "", updated_by, section_id), commit=True)
    return True

def reset_section_to_default(section_id: int, updated_by: Optional[int] = None) -> bool:
    """Reset section content_value to NULL (forcing it to use default_value)."""
    sql = """
        UPDATE site_sections
        SET content_value = NULL,
            updated_by = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    execute_query(sql, (updated_by, section_id), commit=True)
    return True
