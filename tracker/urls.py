from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("eggs/add/", views.egg_add, name="egg_add"),
    path("eggs/", views.egg_list, name="egg_list"),
    path("eggs/<int:pk>/edit/", views.egg_edit, name="egg_edit"),
    path("eggs/<int:pk>/delete/", views.egg_delete, name="egg_delete"),

    path("use/add/", views.egg_use, name="egg_use"),
    path("use/", views.usage_list, name="usage_list"),
    path("use/<int:pk>/edit/", views.egg_use_edit, name="egg_use_edit"),
    path("use/<int:pk>/delete/", views.egg_use_delete, name="egg_use_delete"),

    path("loss/add/", views.mortality_add, name="mortality_add"),
    path("loss/", views.mortality_list, name="mortality_list"),
    path("loss/<int:pk>/edit/", views.mortality_edit, name="mortality_edit"),
    path("loss/<int:pk>/delete/", views.mortality_delete, name="mortality_delete"),

    path("sales/add/", views.sale_add, name="sale_add"),
    path("sales/", views.sale_list, name="sale_list"),
    path("sales/<int:pk>/edit/", views.sale_edit, name="sale_edit"),
    path("sales/<int:pk>/delete/", views.sale_delete, name="sale_delete"),

    path("spend/add/", views.expense_add, name="expense_add"),
    path("spend/", views.expense_list, name="expense_list"),
    path("spend/<int:pk>/edit/", views.expense_edit, name="expense_edit"),
    path("spend/<int:pk>/delete/", views.expense_delete, name="expense_delete"),

    path("batches/", views.batch_list, name="batch_list"),
    path("batches/add/", views.batch_add, name="batch_add"),
    path("batches/<int:pk>/", views.batch_detail, name="batch_detail"),
    path("batches/<int:pk>/edit/", views.batch_edit, name="batch_edit"),

    path("movements/", views.movement_list, name="movement_list"),
    path("movements/add/", views.movement_add, name="movement_add"),
    path("movements/<int:pk>/edit/", views.movement_edit, name="movement_edit"),
    path("movements/<int:pk>/delete/", views.movement_delete, name="movement_delete"),

    path("health/", views.health_list, name="health_list"),
    path("health/add/", views.health_add, name="health_add"),
    path("health/<int:pk>/edit/", views.health_edit, name="health_edit"),
    path("health/<int:pk>/delete/", views.health_delete, name="health_delete"),

    path("feed/", views.feed_page, name="feed"),
    path("feed/<int:pk>/delete/", views.feed_delete, name="feed_delete"),

    path("reports/", views.reports, name="reports"),
    path("more/", views.more, name="more"),

    path("export/", views.export_page, name="export"),
    path("export/all.json", views.export_json, name="export_json"),
    path("export/<str:name>.csv", views.export_csv, name="export_csv"),
]
