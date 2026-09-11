from django import forms
from django.utils import timezone

from .models import (
    Batch, BirdMovement, EggCollection, EggUsage, Expense, FeedUsage,
    HealthRecord, Mortality, Sale,
)


class DateDefaultTodayMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "date" in self.fields and not self.instance.pk:
            self.fields["date"].initial = timezone.localdate()


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ["name", "type", "start_date", "starting_bird_count",
                  "acquisition_cost", "source", "status"]
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"})}


class EggCollectionForm(DateDefaultTodayMixin, forms.ModelForm):
    class Meta:
        model = EggCollection
        fields = ["date", "batch", "eggs_collected", "eggs_cracked"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["batch"].queryset = Batch.objects.filter(type=Batch.LAYER, status=Batch.ACTIVE)


class EggUsageForm(DateDefaultTodayMixin, forms.ModelForm):
    class Meta:
        model = EggUsage
        fields = ["date", "batch", "quantity", "note"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["batch"].queryset = Batch.objects.filter(type=Batch.LAYER, status=Batch.ACTIVE)


class MortalityForm(DateDefaultTodayMixin, forms.ModelForm):
    class Meta:
        model = Mortality
        fields = ["date", "batch", "quantity", "cause"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["batch"].queryset = Batch.objects.filter(status=Batch.ACTIVE)


class SaleForm(DateDefaultTodayMixin, forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["date", "item_type", "batch", "quantity", "unit", "amount_received", "buyer"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["batch"].queryset = Batch.objects.filter(status=Batch.ACTIVE)
        self.fields["unit"].widget.attrs["list"] = "unit-suggestions"


class ExpenseForm(DateDefaultTodayMixin, forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["date", "category", "amount", "note", "batch"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class BirdMovementForm(DateDefaultTodayMixin, forms.ModelForm):
    """Standalone movements: Added / Removed only. Sold goes via Sale."""

    class Meta:
        model = BirdMovement
        fields = ["date", "batch", "type", "quantity", "amount", "source_or_buyer", "notes"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["type"].choices = [
            (BirdMovement.ADDED, "Added"), (BirdMovement.REMOVED, "Removed")]
        self.fields["batch"].queryset = Batch.objects.filter(status=Batch.ACTIVE)


class HealthRecordForm(DateDefaultTodayMixin, forms.ModelForm):
    class Meta:
        model = HealthRecord
        fields = ["date", "batch", "type", "name", "dose_or_quantity",
                  "next_due_date", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "next_due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["batch"].queryset = Batch.objects.filter(status=Batch.ACTIVE)
        self.fields["next_due_date"].required = False


class FeedUsageForm(DateDefaultTodayMixin, forms.ModelForm):
    class Meta:
        model = FeedUsage
        fields = ["date", "batch", "quantity", "unit"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["batch"].queryset = Batch.objects.filter(status=Batch.ACTIVE)
