from django.conf import settings


def farm_settings(request):
    return {
        "CURRENCY": getattr(settings, "FARM_CURRENCY", "GH₵"),
        "FEED_UNIT": getattr(settings, "FEED_UNIT", "kg"),
    }
