"""Views: dashboard, quick entry, lists, reports, export."""

import csv
import json
from datetime import timedelta

from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import calculations as calc
from .forms import (
    BatchForm, BirdMovementForm, EggCollectionForm, EggUsageForm, ExpenseForm,
    FeedUsageForm, HealthRecordForm, MortalityForm, SaleForm,
)
from .models import (
    Batch, BirdMovement, EggCollection, EggUsage, Expense, FeedUsage,
    HealthRecord, Mortality, Sale,
)


# -- dashboard --------------------------------------------------------------

def dashboard(request):
    batches = list(Batch.objects.filter(status=Batch.ACTIVE))
    if not batches and not Batch.objects.exists():
        return redirect("batch_add")
    start = calc.week_start()
    income_w, spent_w, net_w = calc.money_in_range(start)
    due_soon, overdue = calc.health_counts()
    context = {
        "birds": calc.birds_total(batches),
        "batches": [(b, b.current_bird_count()) for b in batches],
        "eggs_today": calc.eggs_today(),
        "eggs_week": calc.eggs_this_week(),
        "egg_stock": calc.egg_stock_total(batches),
        "income_w": income_w,
        "spent_w": spent_w,
        "net_w": net_w,
        "due_soon": due_soon,
        "overdue": overdue,
        "needs_review": [b for b in batches if b.needs_count_review],
        "recent_sales": Sale.objects.all()[:5],
        "recent_eggs": EggCollection.objects.all()[:5],
    }
    return render(request, "tracker/dashboard.html", context)


# -- generic create/edit/delete helpers --------------------------------------

def _save(request, form, success_msg, warn_check=None):
    if form.is_valid():
        obj = form.save()
        warning = warn_check(obj) if warn_check else None
        if warning:
            messages.warning(request, warning)
        else:
            messages.success(request, success_msg)
        return obj
    return None


def _create(request, form_class, template_title, success_msg, warn_check=None, extra=None):
    form = form_class(request.POST or None)
    if request.method == "POST":
        obj = _save(request, form, success_msg, warn_check)
        if obj:
            return redirect("dashboard")
    context = {"form": form, "title": template_title}
    if extra:
        context.update(extra() if callable(extra) else extra)
    return render(request, "tracker/form.html", context)


def _edit(request, obj, form_class, title):
    form = form_class(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Saved.")
        return redirect("dashboard")
    return render(request, "tracker/form.html", {"form": form, "title": title})


@require_POST
def _delete(request, obj, label):
    obj.delete()
    messages.success(request, f"Deleted {label}.")
    return redirect(request.POST.get("next", "dashboard"))


# -- warnings -----------------------------------------------------------------

def egg_sale_warning(sale):
    if sale.item_type == Sale.EGGS:
        stock = sale.batch.egg_stock() + sale.quantity  # stock before this sale
        if sale.quantity > stock:
            return (f"Sale of {sale.quantity} is more than the recorded stock "
                    f"({stock}). Saved anyway — check for missing collections.")
    return None


def count_warning(batch):
    def check(_obj):
        if batch.current_bird_count() < 0:
            return (f"{batch.name} count is below zero. "
                    "Flagged as needing count review — saved anyway.")
        return None
    return check


# -- quick entry ---------------------------------------------------------------

def egg_add(request):
    return _create(request, EggCollectionForm, "Eggs collected", "Eggs saved.")


def egg_edit(request, pk):
    return _edit(request, get_object_or_404(EggCollection, pk=pk), EggCollectionForm, "Edit egg collection")


def egg_delete(request, pk):
    return _delete(request, get_object_or_404(EggCollection, pk=pk), "egg collection")


def egg_use(request):
    return _create(request, EggUsageForm, "Eggs used at home", "Saved.")


def egg_use_edit(request, pk):
    return _edit(request, get_object_or_404(EggUsage, pk=pk), EggUsageForm, "Edit home use")


def egg_use_delete(request, pk):
    return _delete(request, get_object_or_404(EggUsage, pk=pk), "home use")


def mortality_add(request):
    form_class = MortalityForm
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            obj = form.save()
            batch = obj.batch
            if batch.current_bird_count() < 0:
                messages.warning(request, f"{batch.name} count below zero — flagged for review.")
            else:
                messages.success(request, "Saved.")
            return redirect("dashboard")
    else:
        form = form_class()
    return render(request, "tracker/form.html", {"form": form, "title": "Birds lost"})


def mortality_edit(request, pk):
    return _edit(request, get_object_or_404(Mortality, pk=pk), MortalityForm, "Edit loss")


def mortality_delete(request, pk):
    return _delete(request, get_object_or_404(Mortality, pk=pk), "loss record")


def sale_add(request):
    layers = Batch.objects.filter(type=Batch.LAYER, status=Batch.ACTIVE).values("id", "name")
    broilers = Batch.objects.filter(type=Batch.BROILER, status=Batch.ACTIVE).values("id", "name")
    if request.method == "POST":
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save()
            warning = egg_sale_warning(sale)
            if sale.item_type == Sale.BROILER and sale.batch.current_bird_count() < 0:
                warning = f"{sale.batch.name} count below zero — flagged for review."
            if warning:
                messages.warning(request, warning)
            else:
                messages.success(request, "Sale saved.")
            return redirect("dashboard")
    else:
        form = SaleForm()
    return render(request, "tracker/sale_form.html", {
        "form": form, "title": "New sale",
        "layers_json": json.dumps(list(layers)),
        "broilers_json": json.dumps(list(broilers)),
    })


def sale_edit(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    form = SaleForm(request.POST or None, instance=sale)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sale saved.")
        return redirect("dashboard")
    return render(request, "tracker/form.html", {"form": form, "title": "Edit sale"})


def sale_delete(request, pk):
    return _delete(request, get_object_or_404(Sale, pk=pk), "sale")


def expense_add(request):
    return _create(request, ExpenseForm, "New expense", "Expense saved.")


def expense_edit(request, pk):
    return _edit(request, get_object_or_404(Expense, pk=pk), ExpenseForm, "Edit expense")


def expense_delete(request, pk):
    return _delete(request, get_object_or_404(Expense, pk=pk), "expense")


# -- batches --------------------------------------------------------------------

def batch_list(request):
    batches = Batch.objects.all()
    return render(request, "tracker/batch_list.html",
                  {"rows": [(b, b.current_bird_count()) for b in batches]})


def batch_add(request):
    form = BatchForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Batch saved.")
        return redirect("batch_list")
    return render(request, "tracker/form.html", {"form": form, "title": "New batch"})


def batch_edit(request, pk):
    return _edit(request, get_object_or_404(Batch, pk=pk), BatchForm, "Edit batch")


def batch_detail(request, pk):
    b = get_object_or_404(Batch, pk=pk)
    return render(request, "tracker/batch_detail.html", {
        "b": b,
        "count": b.current_bird_count(),
        "added": b.added(), "sold": b.sold(), "removed": b.removed(), "dead": b.dead(),
        "egg_stock": b.egg_stock() if b.type == Batch.LAYER else None,
        "movements": b.movements.all()[:30],
        "mortalities": b.mortalities.all()[:30],
        "eggs": b.egg_collections.all()[:30],
        "usages": b.egg_usages.all()[:30],
        "sales": b.sales.all()[:30],
        "expenses": b.expenses.all()[:30],
        "health": b.health_records.all()[:30],
    })


# -- movements -------------------------------------------------------------------

def movement_list(request):
    return render(request, "tracker/record_list.html", {
        "title": "Bird movements",
        "add_url": "movement_add",
        "rows": BirdMovement.objects.all()[:100],
        "kind": "movement",
    })


def movement_add(request):
    return _create(request, BirdMovementForm, "Add / remove birds", "Saved.")


def movement_edit(request, pk):
    m = get_object_or_404(BirdMovement, pk=pk)
    if m.linked_sale_id:
        messages.error(request, "That entry came from a sale — edit the sale instead.")
        return redirect("movement_list")
    return _edit(request, m, BirdMovementForm, "Edit movement")


def movement_delete(request, pk):
    m = get_object_or_404(BirdMovement, pk=pk)
    if m.linked_sale_id:
        messages.error(request, "That entry came from a sale — delete the sale instead.")
        return redirect("movement_list")
    return _delete(request, m, "movement")


# -- health ------------------------------------------------------------------------

def health_list(request):
    today = timezone.localdate()
    upcoming = today + timedelta(days=7)
    return render(request, "tracker/health_list.html", {
        "records": HealthRecord.objects.all()[:100],
        "today": today, "upcoming": upcoming,
    })


def health_add(request):
    return _create(request, HealthRecordForm, "Vaccine / treatment", "Saved.")


def health_edit(request, pk):
    return _edit(request, get_object_or_404(HealthRecord, pk=pk), HealthRecordForm, "Edit record")


def health_delete(request, pk):
    return _delete(request, get_object_or_404(HealthRecord, pk=pk), "health record")


# -- feed ----------------------------------------------------------------------------

def feed_page(request):
    form = FeedUsageForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Feed use saved.")
        return redirect("feed")
    return render(request, "tracker/feed.html", {
        "form": form,
        "summary": calc.feed_summary(),
        "recent": FeedUsage.objects.all()[:30],
    })


def feed_delete(request, pk):
    obj = get_object_or_404(FeedUsage, pk=pk)
    return _delete(request, obj, "feed entry")


# -- more / lists ----------------------------------------------------------------------

def more(request):
    return render(request, "tracker/more.html")


def egg_list(request):
    return render(request, "tracker/record_list.html", {
        "title": "Egg collections", "add_url": "egg_add",
        "rows": EggCollection.objects.all()[:100], "kind": "eggs",
    })


def usage_list(request):
    return render(request, "tracker/record_list.html", {
        "title": "Eggs used at home", "add_url": "egg_use",
        "rows": EggUsage.objects.all()[:100], "kind": "usage",
    })


def sale_list(request):
    return render(request, "tracker/record_list.html", {
        "title": "Sales", "add_url": "sale_add",
        "rows": Sale.objects.all()[:100], "kind": "sales",
    })


def expense_list(request):
    return render(request, "tracker/record_list.html", {
        "title": "Expenses", "add_url": "expense_add",
        "rows": Expense.objects.all()[:100], "kind": "expenses",
    })


def mortality_list(request):
    return render(request, "tracker/record_list.html", {
        "title": "Losses", "add_url": "mortality_add",
        "rows": Mortality.objects.all()[:100], "kind": "mortality",
    })


# -- reports ------------------------------------------------------------------------------

def reports(request):
    start_s = request.GET.get("start", str(calc.week_start()))
    end_s = request.GET.get("end", str(timezone.localdate()))
    try:
        from datetime import date
        start = date.fromisoformat(start_s)
        end = date.fromisoformat(end_s)
    except ValueError:
        start, end = calc.week_start(), timezone.localdate()
        start_s, end_s = str(start), str(end)

    eggs = list(EggCollection.objects.filter(date__gte=start, date__lte=end)
                .values("date").annotate(good=Sum("eggs_collected"), bad=Sum("eggs_cracked"))
                .order_by("date"))
    sales = list(Sale.objects.filter(date__gte=start, date__lte=end)
                 .values("item_type").annotate(total=Sum("amount_received")))
    expenses = list(Expense.objects.filter(date__gte=start, date__lte=end)
                    .values("category").annotate(total=Sum("amount")))
    mortality = list(Mortality.objects.filter(date__gte=start, date__lte=end)
                     .values("batch__name").annotate(total=Sum("quantity")))
    income, spent, net = calc.money_in_range(start, end)
    flock = [(b, b.current_bird_count()) for b in Batch.objects.filter(status=Batch.ACTIVE)]
    return render(request, "tracker/reports.html", {
        "start": start_s, "end": end_s, "eggs": eggs,
        "sales": sales, "expenses": expenses, "mortality": mortality,
        "income": income, "spent": spent, "net": net, "flock": flock,
    })


# -- export / backup -------------------------------------------------------------------------

EXPORT_MODELS = {
    "batches": Batch, "movements": BirdMovement, "mortality": Mortality,
    "eggs": EggCollection, "egg_usage": EggUsage, "sales": Sale,
    "expenses": Expense, "feed_usage": FeedUsage, "health": HealthRecord,
}


def export_page(request):
    return render(request, "tracker/export.html", {"models": list(EXPORT_MODELS)})


def export_json(request):
    from django.core import serializers
    data = {}
    for name, model in EXPORT_MODELS.items():
        data[name] = json.loads(serializers.serialize("json", model.objects.all()))
    response = HttpResponse(json.dumps(data, indent=2), content_type="application/json")
    response["Content-Disposition"] = (
        f"attachment; filename=farm-backup-{timezone.localdate()}.json")
    return response


def export_csv(request, name):
    model = EXPORT_MODELS.get(name)
    if not model:
        return redirect("export")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={name}-{timezone.localdate()}.csv"
    writer = csv.writer(response)
    fields = [f.name for f in model._meta.fields]
    writer.writerow(fields)
    for obj in model.objects.all():
        writer.writerow([getattr(obj, f) for f in fields])
    return response


def seed_info(request):
    return JsonResponse({"seed_batches": list(
        Batch.objects.filter(is_seed=True).values("name", "type"))})
