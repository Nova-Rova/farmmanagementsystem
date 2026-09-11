from django.contrib import admin

from .models import (
    Batch, BirdMovement, EggCollection, EggUsage, Expense, FeedUsage,
    HealthRecord, Mortality, Sale,
)

admin.site.register(Batch)
admin.site.register(BirdMovement)
admin.site.register(Mortality)
admin.site.register(EggCollection)
admin.site.register(EggUsage)
admin.site.register(Sale)
admin.site.register(Expense)
admin.site.register(FeedUsage)
admin.site.register(HealthRecord)
