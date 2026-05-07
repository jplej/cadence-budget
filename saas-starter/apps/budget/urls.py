from django.urls import path

from . import views

urlpatterns = [
    path("partners/", views.list_partners, name="list_partners"),
    path("partners/<int:partner_id>/edit/", views.edit_partner, name="edit_partner"),
    path("partners/<int:partner_id>/delete/", views.delete_partner, name="delete_partner"),
    path("categories/", views.list_categories, name="list_categories"),
    path("categories/<int:category_id>/edit/", views.edit_category, name="edit_category"),
    path("categories/<int:category_id>/delete/", views.delete_category, name="delete_category"),
]
