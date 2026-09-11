"""Backfill is_seed for sample records created before the flag existed.

Covers records still linked to seed batches, plus seed expenses orphaned
by batch deletion (Expense.batch uses SET_NULL, so --clear's old
batch-only delete left them behind with batch=None).
"""

from django.db import migrations


def flag_seed(apps, schema_editor):
    Batch = apps.get_model("tracker", "Batch")
    seed_batch_ids = list(Batch.objects.filter(is_seed=True).values_list("id", flat=True))
    child_models = ["BirdMovement", "Mortality", "EggCollection", "EggUsage",
                    "Sale", "FeedUsage", "HealthRecord"]
    for name in child_models:
        model = apps.get_model("tracker", name)
        model.objects.filter(batch_id__in=seed_batch_ids).update(is_seed=True)
    Expense = apps.get_model("tracker", "Expense")
    Expense.objects.filter(batch_id__in=seed_batch_ids).update(is_seed=True)
    # Orphans from earlier --clear runs: batch-less expenses with sample notes.
    Expense.objects.filter(batch__isnull=True, note__istartswith="sample").update(is_seed=True)


class Migration(migrations.Migration):
    dependencies = [
        ("tracker", "0002_birdmovement_is_seed_eggcollection_is_seed_and_more"),
    ]

    operations = [
        migrations.RunPython(flag_seed, migrations.RunPython.noop),
    ]
