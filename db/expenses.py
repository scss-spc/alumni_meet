from typing import List, Dict, Any, Optional
from db.connection import execute_query, get_db_cursor

# Organizer-side spending for the meet (catering, mementos, ...). Amounts are stored in INR.
# An expense can be paid in several parts; each part is a row in meet_expense_payments.
EXPENSE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS `meet_expenses` (
        `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
        `meet_id` BIGINT NOT NULL,
        `category` VARCHAR(40) NOT NULL,
        `audience` VARCHAR(20) NOT NULL DEFAULT 'alumni',
        `description` VARCHAR(255) NOT NULL,
        `quantity` INT NULL,
        `unit_cost` DECIMAL(12, 2) NULL,
        `amount` DECIMAL(12, 2) NOT NULL,
        `vendor` VARCHAR(255) NULL,
        `expense_date` DATE NULL,
        `paid_on` DATE NULL,
        `notes` TEXT NULL,
        `created_by` BIGINT NULL,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        KEY `idx_expenses_meet_category` (`meet_id`, `category`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

PAYMENT_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS `meet_expense_payments` (
        `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
        `expense_id` BIGINT NOT NULL,
        `amount` DECIMAL(12, 2) NOT NULL,
        `paid_on` DATE NOT NULL,
        `note` VARCHAR(255) NULL,
        `created_by` BIGINT NULL,
        `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        KEY `idx_expense_payments_expense` (`expense_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

_EXPENSE_COLUMNS = """
    id, meet_id, category, audience, description, quantity, unit_cost, amount, vendor,
    COALESCE(expense_date, DATE(created_at)) AS expense_date, notes, created_by, created_at, updated_at
"""


def ensure_expenses_table() -> None:
    """Create/upgrade the expense tables (additive; safe to run on every start)."""
    execute_query(EXPENSE_TABLE_SQL, commit=True)
    execute_query(PAYMENT_TABLE_SQL, commit=True)
    # Upgrade tables created before "date created" existed.
    execute_query("ALTER TABLE meet_expenses ADD COLUMN IF NOT EXISTS expense_date DATE NULL AFTER vendor", commit=True)
    execute_query("UPDATE meet_expenses SET expense_date = DATE(created_at) WHERE expense_date IS NULL", commit=True)
    # Who the money is spent on (alumni / students / teachers / everyone); older rows were all for alumni.
    execute_query(
        "ALTER TABLE meet_expenses ADD COLUMN IF NOT EXISTS audience VARCHAR(20) NOT NULL DEFAULT 'alumni' AFTER category",
        commit=True)
    # Older single "date paid" values become one full payment (only for expenses with no payments yet).
    execute_query("""
        INSERT INTO meet_expense_payments (expense_id, amount, paid_on, note, created_by)
        SELECT e.id, e.amount, e.paid_on, 'Recorded as paid in full', e.created_by
        FROM meet_expenses e
        WHERE e.paid_on IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM meet_expense_payments p WHERE p.expense_id = e.id)
    """, commit=True)
    execute_query("UPDATE meet_expenses SET paid_on = NULL WHERE paid_on IS NOT NULL", commit=True)


# ---------- expenses ----------

def get_expenses(meet_id: int, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """All expenses for a meet, newest first, optionally filtered by category."""
    sql = f"SELECT {_EXPENSE_COLUMNS} FROM meet_expenses WHERE meet_id = %s"
    params: list = [meet_id]
    if category:
        sql += " AND category = %s"
        params.append(category)
    sql += " ORDER BY COALESCE(expense_date, DATE(created_at)) DESC, id DESC"
    return execute_query(sql, tuple(params), fetch_all=True) or []


def get_expense(expense_id: int) -> Optional[Dict[str, Any]]:
    return execute_query(f"SELECT {_EXPENSE_COLUMNS} FROM meet_expenses WHERE id = %s", (expense_id,), fetch_one=True)


def create_expense(data: Dict[str, Any]) -> int:
    sql = """
        INSERT INTO meet_expenses
            (meet_id, category, audience, description, quantity, unit_cost, amount, vendor, expense_date, notes, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    return execute_query(sql, (
        data["meet_id"], data["category"], data.get("audience") or "alumni", data["description"], data.get("quantity"),
        data.get("unit_cost"), data["amount"], data.get("vendor"), data.get("expense_date"),
        data.get("notes"), data.get("created_by"),
    ), commit=True)


def update_expense(expense_id: int, data: Dict[str, Any]) -> None:
    sql = """
        UPDATE meet_expenses
        SET category = %s, audience = %s, description = %s, quantity = %s, unit_cost = %s, amount = %s,
            vendor = %s, expense_date = %s, notes = %s
        WHERE id = %s
    """
    execute_query(sql, (
        data["category"], data.get("audience") or "alumni", data["description"], data.get("quantity"),
        data.get("unit_cost"), data["amount"], data.get("vendor"), data.get("expense_date"), data.get("notes"), expense_id,
    ), commit=True)


def delete_expense(expense_id: int) -> None:
    """Delete an expense together with its payments (one transaction)."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM meet_expense_payments WHERE expense_id = %s", (expense_id,))
        cursor.execute("DELETE FROM meet_expenses WHERE id = %s", (expense_id,))


# ---------- payments ----------

def get_payments_for_meet(meet_id: int) -> List[Dict[str, Any]]:
    """All payments for a meet's expenses, oldest first (used to work out paid totals and fully-paid dates)."""
    sql = """
        SELECT p.id, p.expense_id, p.amount, p.paid_on, p.note, p.created_by, p.created_at
        FROM meet_expense_payments p
        JOIN meet_expenses e ON e.id = p.expense_id
        WHERE e.meet_id = %s
        ORDER BY p.paid_on ASC, p.id ASC
    """
    return execute_query(sql, (meet_id,), fetch_all=True) or []


def get_payments_for_expense(expense_id: int) -> List[Dict[str, Any]]:
    sql = """
        SELECT id, expense_id, amount, paid_on, note, created_by, created_at
        FROM meet_expense_payments WHERE expense_id = %s ORDER BY paid_on ASC, id ASC
    """
    return execute_query(sql, (expense_id,), fetch_all=True) or []


def get_payment(payment_id: int) -> Optional[Dict[str, Any]]:
    sql = "SELECT id, expense_id, amount, paid_on, note, created_by, created_at FROM meet_expense_payments WHERE id = %s"
    return execute_query(sql, (payment_id,), fetch_one=True)


def create_payment(expense_id: int, amount, paid_on, note: Optional[str], created_by: Optional[int]) -> int:
    sql = """
        INSERT INTO meet_expense_payments (expense_id, amount, paid_on, note, created_by)
        VALUES (%s, %s, %s, %s, %s)
    """
    return execute_query(sql, (expense_id, amount, paid_on, note, created_by), commit=True)


def delete_payment(payment_id: int) -> None:
    execute_query("DELETE FROM meet_expense_payments WHERE id = %s", (payment_id,), commit=True)
