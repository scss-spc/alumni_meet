"""Expense tracking: validation, part payments, per-person maths and template rendering (no database writes)."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from flask import render_template

from app import create_app
from config import Config
from services.expense_service import (
    EXPENSE_AUDIENCES,
    EXPENSE_CATEGORIES,
    apply_payment_status,
    build_expense_summary,
    build_public_expense_summary,
    parse_expense_form,
    parse_payment_form,
    save_expense,
)

STATS = {"total_attending_alumni": 96, "total_headcount": 141, "total_maybe": 14, "maybe_headcount": 20,
         "total_responses": 128, "total_virtual": 8, "total_not_attending": 10, "total_guests": 45}
TODAY = date(2026, 11, 26)


class ExpenseTestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-expenses"
    ADMIN_PATH_PREFIX = "/admin"


def _expense(id_, category, amount, payments=(), **extra):
    row = {"id": id_, "meet_id": 1, "category": category, "description": f"Item {id_}", "quantity": None,
           "unit_cost": None, "amount": Decimal(amount), "vendor": None, "expense_date": date(2026, 11, 20),
           "notes": None}
    row.update(extra)
    pays = [{"id": i, "expense_id": id_, "amount": Decimal(a), "paid_on": d, "note": None}
            for i, (a, d) in enumerate(payments, start=1)]
    return apply_payment_status(row, pays)


# ---------- expense form ----------

def test_amount_is_quantity_times_unit_cost_and_date_created_defaults_to_today():
    data, errors = parse_expense_form(
        {"category": "mementos", "description": "Engraved plaques", "quantity": "96", "unit_cost": "450.50"},
        meet_id=1, today=TODAY)
    assert errors == []
    assert data["amount"] == Decimal("43248.00")
    assert data["expense_date"] == TODAY
    assert data["paid_now"] is None


def test_explicit_amount_date_and_first_payment():
    data, errors = parse_expense_form(
        {"category": "catering", "description": "Dinner buffet", "amount": "₹80,000", "expense_date": "2026-11-01",
         "paid_now": "30000", "paid_now_on": "2026-11-05", "vendor": "  Caterer  "}, meet_id=1, today=TODAY)
    assert errors == []
    assert data["amount"] == Decimal("80000.00")
    assert data["expense_date"] == date(2026, 11, 1)
    assert data["paid_now"] == Decimal("30000.00") and data["paid_now_on"] == date(2026, 11, 5)
    assert data["vendor"] == "Caterer"


def test_first_payment_cannot_exceed_amount():
    _, errors = parse_expense_form({"category": "other", "description": "Misc", "amount": "100", "paid_now": "150"},
                                   meet_id=1, today=TODAY)
    assert any("cannot be more than the expense amount" in e for e in errors)


def test_invalid_input_is_reported():
    _, errors = parse_expense_form({"category": "fireworks", "description": "", "amount": "-5",
                                    "expense_date": "31-31-2026"}, meet_id=1, today=TODAY)
    joined = " ".join(errors)
    assert "valid category" in joined and "Description is required" in joined
    assert "cannot be negative" in joined and "Date created must be a valid date" in joined


def test_missing_or_zero_amount_rejected():
    _, e1 = parse_expense_form({"category": "other", "description": "Misc", "unit_cost": "10"}, meet_id=1)
    _, e2 = parse_expense_form({"category": "other", "description": "Misc", "amount": "0"}, meet_id=1)
    assert any("Enter an amount" in e for e in e1)
    assert any("greater than zero" in e for e in e2)


# ---------- part payments ----------

def test_unpaid_partly_paid_and_fully_paid_dates():
    unpaid = _expense(1, "catering", "1000")
    assert unpaid["payment_status"] == "unpaid" and unpaid["balance_due"] == Decimal("1000.00")
    assert unpaid["fully_paid_on"] is None

    partial = _expense(2, "catering", "1000", payments=[("400", date(2026, 11, 2))])
    assert partial["payment_status"] == "partial"
    assert partial["paid_total"] == Decimal("400.00") and partial["balance_due"] == Decimal("600.00")
    assert partial["fully_paid_on"] is None

    # Fully paid on the date of the payment that cleared the balance, regardless of insertion order.
    paid = _expense(3, "mementos", "1000",
                    payments=[("600", date(2026, 11, 20)), ("400", date(2026, 11, 2))])
    assert paid["payment_status"] == "paid" and paid["balance_due"] == Decimal("0")
    assert paid["fully_paid_on"] == date(2026, 11, 20)
    assert [p["paid_on"] for p in paid["payments"]] == [date(2026, 11, 2), date(2026, 11, 20)]


def test_payment_form_rejects_more_than_due():
    _, errors = parse_payment_form({"amount": "700", "paid_on": "2026-11-21"}, balance_due=Decimal("600"))
    assert any("still due" in e for e in errors)
    payment, ok = parse_payment_form({"amount": "600", "note": "Final"}, balance_due=Decimal("600"), today=TODAY)
    assert ok == [] and payment["amount"] == Decimal("600.00") and payment["paid_on"] == TODAY


def test_create_with_first_payment_records_it():
    data, _ = parse_expense_form({"category": "catering", "description": "High tea", "amount": "5000",
                                  "paid_now": "2000"}, meet_id=1, today=TODAY)
    with patch("services.expense_service.create_expense", return_value=7) as create, \
         patch("services.expense_service.create_payment", return_value=11) as pay, \
         patch("services.expense_service.log_audit_action"):
        new_id, error = save_expense(data, user_id=3)
    assert (new_id, error) == (7, None)
    assert create.call_args[0][0]["created_by"] == 3
    assert pay.call_args[0][:3] == (7, Decimal("2000.00"), TODAY)


def test_cannot_lower_amount_below_what_is_paid():
    existing = _expense(5, "catering", "1000", payments=[("800", date(2026, 11, 2))])
    data, _ = parse_expense_form({"category": "catering", "description": "Dinner", "amount": "500"}, meet_id=1)
    with patch("services.expense_service.get_expense_with_payments", return_value=existing), \
         patch("services.expense_service.update_expense") as update:
        new_id, error = save_expense(data, expense_id=5, user_id=3)
    assert new_id is None and "already paid" in error
    update.assert_not_called()


# ---------- summary maths ----------

def test_summary_committed_paid_due_and_per_person():
    expenses = [
        _expense(1, "catering", "84600", payments=[("50000", date(2026, 11, 2))]),
        _expense(2, "mementos", "43200", payments=[("43200", date(2026, 11, 20))]),
        _expense(3, "printing", "3500"),
    ]
    s = build_expense_summary(1, STATS, funds_contributed=Decimal("150000"), expenses=expenses)
    assert s["total_committed"] == Decimal("131300.00")
    assert s["total_paid"] == Decimal("93200.00")
    assert s["total_due"] == Decimal("38100.00")
    assert s["status_counts"] == {"unpaid": 1, "partial": 1, "paid": 1}
    assert s["catering_per_head"] == Decimal("600.00")      # 84600 / 141 people
    assert s["memento_per_alumnus"] == Decimal("450.00")    # 43200 / 96 alumni
    assert s["balance"] == Decimal("18700.00") and s["cash_in_hand"] == Decimal("56800.00")


def test_summary_handles_no_attendees_and_unknown_category():
    s = build_expense_summary(1, {"total_attending_alumni": 0, "total_headcount": 0}, 0,
                              expenses=[_expense(1, "legacy_cat", "500")])
    assert s["catering_per_head"] is None and s["memento_per_alumnus"] is None
    assert s["total_committed"] == Decimal("500.00")
    assert any(c["key"] == "legacy_cat" for c in s["by_category"])


# ---------- templates render with sample data ----------

def test_expenses_page_renders_dates_status_and_payments():
    app = create_app(ExpenseTestConfig)
    expenses = [
        _expense(1, "catering", "84600", payments=[("50000", date(2026, 11, 2))], description="Dinner buffet"),
        _expense(2, "mementos", "43200", payments=[("20000", date(2026, 11, 3)), ("23200", date(2026, 11, 22))],
                 description="Engraved plaques", quantity=96, unit_cost=Decimal("450.00")),
    ]
    summary = build_expense_summary(1, STATS, Decimal("150000"), expenses=expenses)
    with app.test_request_context("/"):
        html = render_template("admin/expenses.html", meet={"name": "Continuum"}, meet_stats=STATS,
                               summary=summary, expenses=expenses, categories=EXPENSE_CATEGORIES,
                               audiences=EXPENSE_AUDIENCES, current_category="", current_audience="")
    assert "Date Created" in html and "Fully Paid On" in html
    assert "Partly paid" in html and "₹34,600.00 due" in html
    assert "22 Nov 2026" in html          # fully paid on the clearing payment's date
    assert "2 payments" in html
    assert "96 alumni + 45 family &amp; guests" in html


def test_dashboard_shows_alumni_and_headcount_split():
    app = create_app(ExpenseTestConfig)
    summary = build_expense_summary(1, STATS, 0, expenses=[])
    with app.test_request_context("/"):
        html = render_template(
            "admin/dashboard.html", meet={"name": "Continuum"}, meet_stats=STATS,
            financial_stats={"total_submissions": 0, "total_submitted_amount": 0, "distinct_contributors": 0},
            recent_contributions=[], recent_responses=[], audit_logs=[],
            sync_state={}, scheduler_info={}, expense_summary=summary)
    assert "Alumni Attending · Mementos" in html
    assert "Total Headcount · Catering" in html
    assert "96 alumni + 45 family &amp; guests" in html


# ---------- who the money is spent on (alumni / students / teachers) ----------

def test_audience_defaults_to_alumni_and_rejects_unknown():
    data, errors = parse_expense_form({"category": "other", "description": "Misc", "amount": "100"}, meet_id=1)
    assert errors == [] and data["audience"] == "alumni"
    data, errors = parse_expense_form({"category": "mementos", "description": "Faculty shawls", "amount": "9000",
                                       "audience": "teachers"}, meet_id=1)
    assert errors == [] and data["audience"] == "teachers"
    _, errors = parse_expense_form({"category": "other", "description": "Misc", "amount": "100",
                                    "audience": "aliens"}, meet_id=1)
    assert any("who the expense is for" in e for e in errors)


def test_summary_splits_by_audience_and_memento_per_alumnus_counts_alumni_only():
    expenses = [
        _expense(1, "mementos", "43200", audience="alumni"),
        _expense(2, "mementos", "9000", audience="teachers"),
        _expense(3, "catering", "12000", audience="students"),
        _expense(4, "printing", "500"),  # legacy row without audience -> alumni
    ]
    s = build_expense_summary(1, STATS, 0, expenses=expenses)
    by_aud = {a["key"]: a["total"] for a in s["by_audience"]}
    assert by_aud == {"alumni": Decimal("43700.00"), "students": Decimal("12000.00"),
                      "teachers": Decimal("9000.00"), "all": Decimal("0")}
    assert s["mementos_total"] == Decimal("52200.00")
    assert s["memento_per_alumnus"] == Decimal("450.00")  # 43200 / 96, teacher mementos excluded


def test_public_summary_shortfall_allocations_and_no_private_fields():
    expenses = [
        _expense(1, "catering", "60000", payments=[("20000", date(2026, 11, 2))], audience="all",
                 vendor="Secret Caterers", notes="internal invoice 42"),
        _expense(2, "mementos", "30000", audience="teachers"),
        _expense(3, "printing", "10000", audience="students"),
    ]
    p = build_public_expense_summary(1, funds_contributed=75000, expenses=expenses)
    assert p["total_committed"] == Decimal("100000.00")
    assert p["shortfall"] == Decimal("25000.00") and p["surplus"] == Decimal("0")
    assert p["funded_percent"] == 75.0
    assert [c["key"] for c in p["by_category"]] == ["catering", "mementos", "printing"]  # largest first, empty dropped
    assert p["by_category"][0]["percent"] == 60.0 and p["by_category"][0]["due"] == Decimal("40000.00")
    assert {a["key"] for a in p["by_audience"]} == {"all", "teachers", "students"}
    for item in p["line_items"]:
        assert "vendor" not in item and "notes" not in item

    covered = build_public_expense_summary(1, funds_contributed=120000, expenses=expenses)
    assert covered["shortfall"] == Decimal("0") and covered["surplus"] == Decimal("20000.00")
    assert covered["funded_percent"] == 100.0


def test_public_expenses_page_renders_without_private_details():
    app = create_app(ExpenseTestConfig)
    expenses = [_expense(1, "mementos", "30000", audience="teachers", description="Faculty felicitation",
                         vendor="Secret Vendor", notes="internal note")]
    with app.test_client() as client,             patch("routes.public.get_current_meet_context",
                  return_value={"meet": {"id": 1, "name": "Continuum"}, "stats": {}}),             patch("routes.public.get_public_contributions_tracker",
                  return_value={"stats": {"total_raised": 10000.0, "total_contributors": 4}, "contributors": []}),             patch("services.expense_service.list_expenses", return_value=expenses):
        res = client.get("/expenses")
    html = res.get_data(as_text=True)
    assert res.status_code == 200
    assert "Current Shortfall" in html and "₹20,000.00" in html
    assert "Faculty felicitation" in html and "Teachers" in html
    assert "Secret Vendor" not in html and "internal note" not in html
