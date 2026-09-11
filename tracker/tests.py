from django.core.management import call_command
from django.test import TestCase

from .models import (
    Batch, BirdMovement, EggCollection, EggUsage, Expense, FeedUsage,
    HealthRecord, Mortality, Sale,
)

ALL_MODELS = (Batch, BirdMovement, Mortality, EggCollection, EggUsage,
              Sale, Expense, FeedUsage, HealthRecord)


def counts():
    return {m.__name__: m.objects.count() for m in ALL_MODELS}


class SeedDemoTests(TestCase):
    def test_seed_then_clear_leaves_nothing(self):
        call_command("seed_demo")
        seeded = counts()
        self.assertGreater(seeded["Batch"], 0)
        self.assertGreater(seeded["Expense"], 0)
        # Second seed run must refuse, not duplicate.
        call_command("seed_demo")
        self.assertEqual(counts(), seeded)
        # Clear must remove everything, including batch-less expenses
        # (Expense.batch is SET_NULL, so no cascade).
        call_command("seed_demo", "--clear")
        self.assertEqual(counts(), {m.__name__: 0 for m in ALL_MODELS})

    def test_broiler_sale_keeps_movement_in_sync(self):
        call_command("seed_demo")
        broilers = Batch.objects.get(type=Batch.BROILER, is_seed=True)
        before = broilers.current_bird_count()
        sale = Sale.objects.create(
            batch=broilers, item_type=Sale.BROILER, quantity=2,
            unit="birds", amount_received=100)
        self.assertEqual(
            BirdMovement.objects.get(linked_sale=sale).quantity, 2)
        self.assertEqual(broilers.current_bird_count(), before - 2)
        pk = sale.pk
        sale.delete()
        # NB: sale.pk is unusable after delete; capture it first.
        self.assertFalse(BirdMovement.objects.filter(linked_sale_id=pk).exists())
