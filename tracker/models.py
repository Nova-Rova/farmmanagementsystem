"""Core data model. Running totals are never stored; they are derived."""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone


non_negative = MinValueValidator(0)


class Batch(models.Model):
    LAYER = "Layer"
    BROILER = "Broiler"
    TYPE_CHOICES = [(LAYER, "Layer"), (BROILER, "Broiler")]

    ACTIVE = "Active"
    CLOSED = "Closed"
    STATUS_CHOICES = [(ACTIVE, "Active"), (CLOSED, "Closed")]

    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    start_date = models.DateField(default=timezone.localdate)
    starting_bird_count = models.PositiveIntegerField(validators=[non_negative])
    acquisition_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[non_negative])
    source = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ACTIVE)
    is_seed = models.BooleanField(default=False, help_text="Sample data. Delete before real use.")

    class Meta:
        ordering = ["-start_date", "name"]

    def __str__(self):
        return self.name

    # -- derived values (never stored) -------------------------------------
    def added(self):
        return self.movements.filter(type=BirdMovement.ADDED).aggregate(
            s=models.Sum("quantity"))["s"] or 0

    def sold(self):
        return self.movements.filter(type=BirdMovement.SOLD).aggregate(
            s=models.Sum("quantity"))["s"] or 0

    def removed(self):
        return self.movements.filter(type=BirdMovement.REMOVED).aggregate(
            s=models.Sum("quantity"))["s"] or 0

    def dead(self):
        return self.mortalities.aggregate(s=models.Sum("quantity"))["s"] or 0

    def current_bird_count(self):
        return self.starting_bird_count + self.added() - self.sold() - self.removed() - self.dead()

    @property
    def needs_count_review(self):
        return self.current_bird_count() < 0

    def egg_stock(self):
        """Only meaningful for Layer batches."""
        collected = self.egg_collections.aggregate(s=models.Sum("eggs_collected"))["s"] or 0
        cracked = self.egg_collections.aggregate(s=models.Sum("eggs_cracked"))["s"] or 0
        sold_eggs = self.sales.filter(item_type=Sale.EGGS).aggregate(s=models.Sum("quantity"))["s"] or 0
        used = self.egg_usages.aggregate(s=models.Sum("quantity"))["s"] or 0
        return collected - cracked - sold_eggs - used


class BirdMovement(models.Model):
    ADDED = "Added"
    SOLD = "Sold"
    REMOVED = "Removed"
    TYPE_CHOICES = [(ADDED, "Added"), (SOLD, "Sold"), (REMOVED, "Removed")]

    date = models.DateField(default=timezone.localdate)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="movements")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField(validators=[non_negative])
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[non_negative])
    source_or_buyer = models.CharField(max_length=200, blank=True)
    notes = models.CharField(max_length=300, blank=True)
    linked_sale = models.OneToOneField(
        "Sale", on_delete=models.CASCADE, null=True, blank=True, related_name="linked_movement")

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} {self.batch} {self.type} x{self.quantity}"


class Mortality(models.Model):
    date = models.DateField(default=timezone.localdate)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="mortalities")
    quantity = models.PositiveIntegerField(validators=[non_negative])
    cause = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name_plural = "mortality records"

    def __str__(self):
        return f"{self.date} {self.batch} died x{self.quantity}"


class EggCollection(models.Model):
    date = models.DateField(default=timezone.localdate)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="egg_collections",
                              limit_choices_to={"type": Batch.LAYER})
    eggs_collected = models.PositiveIntegerField(validators=[non_negative])
    eggs_cracked = models.PositiveIntegerField(default=0, validators=[non_negative])

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} {self.batch} +{self.eggs_collected} eggs"

    def clean(self):
        if self.batch_id and self.batch.type != Batch.LAYER:
            raise ValidationError("Eggs can only be collected from a Layer batch.")


class EggUsage(models.Model):
    """Eggs eaten at home or given away. Reduces egg stock, not a sale."""

    date = models.DateField(default=timezone.localdate)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="egg_usages",
                              limit_choices_to={"type": Batch.LAYER})
    quantity = models.PositiveIntegerField(validators=[non_negative])
    note = models.CharField(max_length=300, blank=True, help_text="e.g. home use, given to family")

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} {self.batch} used x{self.quantity}"

    def clean(self):
        if self.batch_id and self.batch.type != Batch.LAYER:
            raise ValidationError("Only a Layer batch has eggs to use.")


class Sale(models.Model):
    EGGS = "Eggs"
    BROILER = "Broiler"
    ITEM_CHOICES = [(EGGS, "Eggs"), (BROILER, "Broiler")]

    date = models.DateField(default=timezone.localdate)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="sales")
    item_type = models.CharField(max_length=10, choices=ITEM_CHOICES)
    quantity = models.PositiveIntegerField(validators=[non_negative])
    unit = models.CharField(max_length=30, default="count")
    amount_received = models.DecimalField(max_digits=12, decimal_places=2, validators=[non_negative])
    buyer = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} {self.item_type} x{self.quantity} ({self.amount_received})"

    def clean(self):
        if self.batch_id:
            if self.item_type == self.EGGS and self.batch.type != Batch.LAYER:
                raise ValidationError("Egg sales must use a Layer batch.")
            if self.item_type == self.BROILER and self.batch.type != Batch.BROILER:
                raise ValidationError("Broiler sales must use a Broiler batch.")

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.item_type == self.BROILER:
                # One form, two records: keep the linked Sold movement in sync.
                BirdMovement.objects.update_or_create(
                    linked_sale=self,
                    defaults={
                        "date": self.date,
                        "batch": self.batch,
                        "type": BirdMovement.SOLD,
                        "quantity": self.quantity,
                        "amount": self.amount_received,
                        "source_or_buyer": self.buyer,
                    },
                )
            else:
                BirdMovement.objects.filter(linked_sale=self).delete()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            BirdMovement.objects.filter(linked_sale=self).delete()
            super().delete(*args, **kwargs)


class Expense(models.Model):
    FEED = "Feed"
    MEDICINE = "Medicine"
    EQUIPMENT = "Equipment"
    LABOR = "Labor"
    OTHER = "Other"
    CATEGORY_CHOICES = [(c, c) for c in (FEED, MEDICINE, EQUIPMENT, LABOR, OTHER)]

    date = models.DateField(default=timezone.localdate)
    category = models.CharField(max_length=15, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[non_negative])
    note = models.CharField(max_length=300, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses")

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} {self.category} ({self.amount})"


class FeedUsage(models.Model):
    """Optional daily feed consumption. Never required."""

    date = models.DateField(default=timezone.localdate)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="feed_usages")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[non_negative])
    unit = models.CharField(max_length=10, default="kg")

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} {self.batch} {self.quantity}{self.unit}"


class HealthRecord(models.Model):
    VACCINATION = "Vaccination"
    MEDICINE = "Medicine"
    TREATMENT = "Treatment"
    TYPE_CHOICES = [(VACCINATION, "Vaccination"), (MEDICINE, "Medicine"), (TREATMENT, "Treatment")]

    date = models.DateField(default=timezone.localdate)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="health_records")
    type = models.CharField(max_length=12, choices=TYPE_CHOICES)
    name = models.CharField(max_length=200)
    dose_or_quantity = models.CharField(max_length=100, blank=True)
    next_due_date = models.DateField(null=True, blank=True,
                                     help_text="Only from your vet or the product label.")
    notes = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} {self.batch} {self.type}: {self.name}"
