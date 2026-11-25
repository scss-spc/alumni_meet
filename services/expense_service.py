import json
import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple

from db.audit import log_audit_action
from db.expenses import (
    create_expense,
    create_payment,
    delete_expense,
    delete_payment,
    get_expense,
    get_expenses,
    get_payment,
    get_payments_for_expense,
    get_payments_for_meet,
    update_expense,
)

logger = logging.getLogger(__name__)

# Spending categories. Catering scales with total headcount (alumni + family/guests);
# mementos are for alumni only, so they scale with the number of attending alumni.
EXPENSE_CATEGORIES: Dict[str, str] = {
    "catering": "Catering (food & high tea)",
    "mementos": "Mementos (alumni only)",
    "venue": "Venue & Décor",
    "printing": "Printing & Stationery",
    "other": "Other",
}

PAYMENT_STATUS_LABELS = {"unpaid": "Unpaid", "partial": "Partly paid", "paid": "Paid"}

_PAISE = Decimal("0.01")
_ZERO = Decimal("0")


def category_label(key: str) -> str:
    return EXPENSE_CATEGORIES.get(key, key.title() if key else "Other")


def _money(value: Any) -> Decimal:
    return Decimal(str(value or 0)).quantize(_PAISE, rounding=ROUND_HALF_UP)


# ---------- form parsing ----------

def _to_decimal(raw: Optional[str], field: str, errors: List[str]) -> Optional[Decimal]:
    raw = (raw or "").strip().replace(",", "").replace("₹", "")
    if not raw:
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation:
        errors.append(f"{field} must be a number.")
        return None
    if value < 0:
        errors.append(f"{field} cannot be negative.")
        return None
    return value.quantize(_PAISE, rounding=ROUND_HALF_UP)


def _to_int(raw: Optional[str], field: str, errors: List[str]) -> Optional[int]:
    raw = (raw or "").strip().replace(",", "")
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        errors.append(f"{field} must be a whole number.")
        return None
    if value < 0:
        errors.append(f"{field} cannot be negative.")
        return None
    return value


def _to_date(raw: Optional[str], field: str, errors: List[str]) -> Optional[date]:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        errors.append(f"{field} must be a valid date.")
        return None


def parse_expense_form(form: Dict[str, Any], meet_id: int,
                       today: Optional[date] = None) -> Tuple[Dict[str, Any], List[str]]:
    """Validate the add/edit form. If amount is blank it is computed as quantity × unit cost.

    The optional "paid_now" / "paid_now_on" fields record a first payment (part or full) when adding.
    """
    today = today or date.today()
    errors: List[str] = []
    category = (form.get("category") or "").strip()
    if category not in EXPENSE_CATEGORIES:
        errors.append("Choose a valid category.")

    description = (form.get("description") or "").strip()
    if not description:
        errors.append("Description is required.")
    elif len(description) > 255:
        errors.append("Description must be 255 characters or fewer.")

    quantity = _to_int(form.get("quantity"), "Quantity", errors)
    unit_cost = _to_decimal(form.get("unit_cost"), "Unit cost", errors)
    amount = _to_decimal(form.get("amount"), "Amount", errors)
    if amount is None and quantity is not None and unit_cost is not None:
        amount = (unit_cost * quantity).quantize(_PAISE, rounding=ROUND_HALF_UP)
    if amount is None and not errors:
        errors.append("Enter an amount, or both quantity and unit cost.")
    elif amount is not None and amount <= 0:
        errors.append("Amount must be greater than zero.")

    expense_date = _to_date(form.get("expense_date"), "Date created", errors) or today

    paid_now = _to_decimal(form.get("paid_now"), "Amount paid now", errors)
    paid_now_on = _to_date(form.get("paid_now_on"), "Payment date", errors) or today
    if paid_now is not None and paid_now > 0 and amount is not None and paid_now > amount:
        errors.append("Amount paid now cannot be more than the expense amount.")

    data = {
        "meet_id": meet_id,
        "category": category,
        "description": description,
        "quantity": quantity,
        "unit_cost": unit_cost,
        "amount": amount,
        "vendor": (form.get("vendor") or "").strip() or None,
        "expense_date": expense_date,
        "notes": (form.get("notes") or "").strip() or None,
        "paid_now": paid_now if paid_now and paid_now > 0 else None,
        "paid_now_on": paid_now_on,
    }
    return data, errors


def parse_payment_form(form: Dict[str, Any], balance_due: Decimal,
                       today: Optional[date] = None) -> Tuple[Dict[str, Any], List[str]]:
    """Validate a part/full payment against what is still due."""
    errors: List[str] = []
    amount = _to_decimal(form.get("amount"), "Payment amount", errors)
    if amount is None and not errors:
        errors.append("Enter the payment amount.")
    elif amount is not None and amount <= 0:
        errors.append("Payment amount must be greater than zero.")
    elif amount is not None and amount > balance_due:
        errors.append(f"Payment cannot be more than the ₹{balance_due:,.2f} still due.")
    paid_on = _to_date(form.get("paid_on"), "Payment date", errors) or (today or date.today())
    note = (form.get("note") or "").strip()[:255] or None
    return {"amount": amount, "paid_on": paid_on, "note": note}, errors


# ---------- payment status ----------

def apply_payment_status(expense: Dict[str, Any], payments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Attach payments, paid total, balance due, status and the date it became fully paid."""
    amount = _money(expense.get("amount"))
    ordered = sorted(payments, key=lambda p: (p.get("paid_on") or date.min, p.get("id") or 0))
    running = _ZERO
    fully_paid_on = None
    for p in ordered:
        running += _money(p.get("amount"))
        if fully_paid_on is None and amount > 0 and running >= amount:
            fully_paid_on = p.get("paid_on")
    paid_total = running
    if paid_total <= 0:
        status = "unpaid"
    elif paid_total < amount:
        status = "partial"
    else:
        status = "paid"
    expense.update({
        "payments": ordered,
        "paid_total": paid_total,
        "balance_due": max(amount - paid_total, _ZERO),
        "payment_status": status,
        "payment_status_label": PAYMENT_STATUS_LABELS[status],
        "fully_paid_on": fully_paid_on if status == "paid" else None,
        "category_label": category_label(expense.get("category")),
    })
    return expense


def list_expenses(meet_id: int, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Expenses with their payments and payment status."""
    rows = get_expenses(meet_id, category=category)
    by_expense: Dict[int, List[Dict[str, Any]]] = {}
    for p in get_payments_for_meet(meet_id):
        by_expense.setdefault(p["expense_id"], []).append(p)
    return [apply_payment_status(r, by_expense.get(r["id"], [])) for r in rows]


def get_expense_with_payments(expense_id: int) -> Optional[Dict[str, Any]]:
    expense = get_expense(expense_id)
    if not expense:
        return None
    return apply_payment_status(expense, get_payments_for_expense(expense_id))


# ---------- writes (audited) ----------

def _audit_payload(data: Dict[str, Any]) -> str:
    keep = ("category", "description", "quantity", "unit_cost", "amount", "vendor", "expense_date")
    return json.dumps({k: data.get(k) for k in keep}, default=str)


def _safe_audit(action: str, entity_type: str, entity_id: Optional[int], user_id: Optional[int],
                old: Optional[str], new: Optional[str]):
    try:
        log_audit_action(action, entity_type, entity_id=entity_id, user_id=user_id, old_value=old, new_value=new)
    except Exception as e:  # auditing must never block the organizer's change
        logger.warning(f"Could not write audit log for {action}: {e}")


def save_expense(data: Dict[str, Any], expense_id: Optional[int] = None,
                 user_id: Optional[int] = None) -> Tuple[Optional[int], Optional[str]]:
    """Create or update an expense. Returns (id, error). On create, records the optional first payment."""
    if expense_id:
        old = get_expense_with_payments(expense_id)
        if not old:
            return None, "Expense not found."
        if data["amount"] < old["paid_total"]:
            return None, f"Amount cannot be less than the ₹{old['paid_total']:,.2f} already paid."
        update_expense(expense_id, data)
        _safe_audit("UPDATE_EXPENSE", "meet_expense", expense_id, user_id, _audit_payload(old), _audit_payload(data))
        return expense_id, None

    new_id = create_expense(dict(data, created_by=user_id))
    _safe_audit("CREATE_EXPENSE", "meet_expense", new_id, user_id, None, _audit_payload(data))
    if data.get("paid_now"):
        add_payment(new_id, {"amount": data["paid_now"], "paid_on": data["paid_now_on"], "note": None}, user_id)
    return new_id, None


def add_payment(expense_id: int, payment: Dict[str, Any], user_id: Optional[int] = None) -> int:
    payment_id = create_payment(expense_id, payment["amount"], payment["paid_on"], payment.get("note"), user_id)
    _safe_audit("ADD_EXPENSE_PAYMENT", "meet_expense", expense_id, user_id, None,
                json.dumps({"payment_id": payment_id, **payment}, default=str))
    return payment_id


def remove_payment(payment_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    old = get_payment(payment_id)
    if not old:
        return None
    delete_payment(payment_id)
    _safe_audit("DELETE_EXPENSE_PAYMENT", "meet_expense", old["expense_id"], user_id,
                json.dumps(old, default=str), None)
    return old


def remove_expense(expense_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Delete an expense and its payments; returns the deleted row, or None if it did not exist."""
    old = get_expense_with_payments(expense_id)
    if not old:
        return None
    delete_expense(expense_id)
    _safe_audit("DELETE_EXPENSE", "meet_expense", expense_id, user_id, _audit_payload(old), None)
    return old


# ---------- summary ----------

def build_expense_summary(meet_id: int, meet_stats: Dict[str, Any], funds_contributed: Any = 0,
                          expenses: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Committed / paid / due per category plus per-person figures for the people the money is spent on."""
    expenses = expenses if expenses is not None else list_expenses(meet_id)
    alumni = int(meet_stats.get("total_attending_alumni") or 0)
    headcount = int(meet_stats.get("total_headcount") or 0)

    cats: Dict[str, Dict[str, Any]] = {
        key: {"key": key, "label": label, "total": _ZERO, "paid": _ZERO, "entries": 0}
        for key, label in EXPENSE_CATEGORIES.items()
    }
    status_counts = {"unpaid": 0, "partial": 0, "paid": 0}
    for e in expenses:
        if "paid_total" not in e:
            apply_payment_status(e, e.get("payments") or [])
        key = e.get("category") or "other"
        c = cats.setdefault(key, {"key": key, "label": category_label(key), "total": _ZERO, "paid": _ZERO, "entries": 0})
        c["total"] += _money(e.get("amount"))
        c["paid"] += e["paid_total"]
        c["entries"] += 1
        status_counts[e["payment_status"]] += 1

    by_category = list(cats.values())
    committed = sum((c["total"] for c in by_category), _ZERO)
    paid = sum((c["paid"] for c in by_category), _ZERO)
    catering = cats["catering"]["total"]
    mementos = cats["mementos"]["total"]
    funds = _money(funds_contributed)

    def per(amount: Decimal, people: int) -> Optional[Decimal]:
        return (amount / people).quantize(_PAISE, rounding=ROUND_HALF_UP) if people else None

    return {
        "by_category": by_category,
        "total_spent": committed,          # total committed (all expenses), kept for the dashboard
        "total_committed": committed,
        "total_paid": paid,
        "total_due": committed - paid,
        "status_counts": status_counts,
        "alumni_attending": alumni,
        "headcount": headcount,
        "family_and_guests": max(headcount - alumni, 0),
        "catering_total": catering,
        "mementos_total": mementos,
        "catering_per_head": per(catering, headcount),
        "memento_per_alumnus": per(mementos, alumni),
        "spent_per_alumnus": per(committed, alumni),
        "funds_contributed": funds,
        "balance": funds - committed,
        "cash_in_hand": funds - paid,
    }
