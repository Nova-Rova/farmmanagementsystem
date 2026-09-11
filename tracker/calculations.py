"""Derived values. Everything here is computed from raw records."""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from .models import EggCollection, EggUsage, Expense, HealthRecord, Mortality, Sale


def week_start():
    today = timezone.localdate()
    return today - timedelta(days=today.weekday())


def eggs_today():
    today = timezone.localdate()
    rows = EggCollection.objects.filter(date=today).aggregate(
        good=Sum("eggs_collected"), bad=Sum("eggs_cracked"))
    return (rows["good"] or 0) - (rows["bad"] or 0)


def eggs_this_week():
    start = week_start()
    rows = EggCollection.objects.filter(date__gte=start).aggregate(
        good=Sum("eggs_collected"), bad=Sum("eggs_cracked"))
    return (rows["good"] or 0) - (rows["bad"] or 0)


def egg_stock_total(batches):
    return sum(b.egg_stock() for b in batches if b.type == "Layer")


def birds_total(batches):
    return sum(b.current_bird_count() for b in batches)


def money_in_range(start, end=None):
    sales = Sale.objects.filter(date__gte=start)
    expenses = Expense.objects.filter(date__gte=start)
    if end:
        sales = sales.filter(date__lte=end)
        expenses = expenses.filter(date__lte=end)
    income = sales.aggregate(s=Sum("amount_received"))["s"] or Decimal("0")
    spent = expenses.aggregate(s=Sum("amount"))["s"] or Decimal("0")
    return income, spent, income - spent


def health_counts():
    """Counts only; never recommendations. Buckets per spec."""
    today = timezone.localdate()
    upcoming = today + timedelta(days=7)
    qs = HealthRecord.objects.exclude(next_due_date__isnull=True)
    overdue = qs.filter(next_due_date__lt=today).count()
    due_soon = qs.filter(next_due_date__gte=today, next_due_date__lte=upcoming).count()
    return due_soon, overdue


def feed_summary():
    """Honest feed picture.

    Feed purchases are recorded as money (Expense), feed use as quantity,
    so an exact quantity stock cannot be known. Show spend, used amounts
    per unit, and whether usage logging is recent. Never invent a number.
    """
    from .models import Expense, FeedUsage

    today = timezone.localdate()
    spent = Expense.objects.filter(category="Feed").aggregate(s=Sum("amount"))["s"] or Decimal("0")
    used_by_unit = list(
        FeedUsage.objects.values("unit").annotate(total=Sum("quantity")).order_by("unit")
    )
    recent = FeedUsage.objects.filter(date__gte=today - timedelta(days=5)).exists()
    has_any = FeedUsage.objects.exists()
    if not has_any:
        stock_label = "Unknown"
    elif not recent:
        stock_label = "Estimated — no use logged in 5 days"
    else:
        stock_label = "Estimated"
    return {
        "spent": spent,
        "used_by_unit": used_by_unit,
        "recent": recent,
        "has_any": has_any,
        "stock_label": stock_label,
    }
