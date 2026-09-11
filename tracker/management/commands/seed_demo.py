"""Sample data so the dashboard makes sense before real records exist.

Run: python manage.py seed_demo
Remove: python manage.py seed_demo --clear
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from tracker.models import (
    Batch, BirdMovement, EggCollection, EggUsage, Expense, FeedUsage,
    HealthRecord, Mortality, Sale,
)


class Command(BaseCommand):
    help = "Create (or clear with --clear) sample data."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Delete sample data.")

    def handle(self, *args, **options):
        if options["clear"]:
            n, _ = Batch.objects.filter(is_seed=True).delete()
            self.stdout.write(self.style.SUCCESS(f"Removed sample data ({n} objects)."))
            return
        if Batch.objects.filter(is_seed=True).exists():
            self.stdout.write("Sample data already exists. Use --clear first.")
            return

        today = timezone.localdate()
        layers = Batch.objects.create(
            name="Layers-Batch-01", type=Batch.LAYER, start_date=today - timedelta(days=60),
            starting_bird_count=6, source="Home stock", is_seed=True)
        broilers = Batch.objects.create(
            name="Broilers-Batch-01", type=Batch.BROILER, start_date=today - timedelta(days=20),
            starting_bird_count=50, acquisition_cost=Decimal("800.00"),
            source="Sample supplier", is_seed=True)

        for i in range(7):
            d = today - timedelta(days=i)
            EggCollection.objects.create(
                date=d, batch=layers, eggs_collected=5 if i else 4,
                eggs_cracked=1 if i == 2 else 0)
        Mortality.objects.create(date=today - timedelta(days=10), batch=layers,
                                 quantity=1, cause="Sample: illness")
        Mortality.objects.create(date=today - timedelta(days=3), batch=broilers,
                                 quantity=2, cause="Sample: heat")
        HealthRecord.objects.create(
            date=today - timedelta(days=30), batch=layers, type="Vaccination",
            name="Sample Newcastle vaccine", next_due_date=today + timedelta(days=3))
        HealthRecord.objects.create(
            date=today - timedelta(days=40), batch=broilers, type="Medicine",
            name="Sample vitamins", next_due_date=today - timedelta(days=2))
        Expense.objects.create(date=today - timedelta(days=5), category="Feed",
                               amount=Decimal("150.00"), note="Sample feed", batch=layers)
        Expense.objects.create(date=today - timedelta(days=2), category="Medicine",
                               amount=Decimal("40.00"), note="Sample medicine")
        Sale.objects.create(date=today - timedelta(days=1), batch=layers, item_type="Eggs",
                            quantity=10, unit="count", amount_received=Decimal("20.00"))
        Sale.objects.create(date=today, batch=broilers, item_type="Broiler",
                            quantity=3, unit="birds", amount_received=Decimal("180.00"))
        EggUsage.objects.create(date=today - timedelta(days=1), batch=layers,
                                quantity=4, note="Sample: home use")
        BirdMovement.objects.create(date=today - timedelta(days=15), batch=broilers,
                                    type=BirdMovement.ADDED, quantity=5, notes="Sample top-up")
        FeedUsage.objects.create(date=today, batch=layers, quantity=Decimal("2.50"), unit="kg")
        self.stdout.write(self.style.SUCCESS("Sample data created."))
