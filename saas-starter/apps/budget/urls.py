from django.urls import path

from . import views

urlpatterns = [
    path("partners/", views.list_partners, name="list_partners"),
    path("partners/<int:partner_id>/edit/", views.edit_partner, name="edit_partner"),
    path("partners/<int:partner_id>/delete/", views.delete_partner, name="delete_partner"),
    path("categories/", views.list_categories, name="list_categories"),
    path("categories/<int:category_id>/edit/", views.edit_category, name="edit_category"),
    path("categories/<int:category_id>/delete/", views.delete_category, name="delete_category"),
    path("projects/", views.list_projects, name="list_projects"),
    path("projects/new/", views.edit_project, name="new_project"),
    path("projects/<int:project_id>/", views.project_detail, name="project_detail"),
    path("projects/<int:project_id>/edit/", views.edit_project, name="edit_project"),
    path("projects/<int:project_id>/delete/", views.delete_project, name="delete_project"),
    path("projects/<int:project_id>/settings/", views.project_settings, name="project_settings"),
    path("projects/<int:project_id>/participations/add/", views.add_participation, name="add_participation"),
    path("projects/<int:project_id>/participations/<int:part_id>/edit/", views.edit_participation, name="edit_participation"),
    path("projects/<int:project_id>/participations/<int:part_id>/delete/", views.delete_participation, name="delete_participation"),
    path("projects/<int:project_id>/waterfall/", views.waterfall_results, name="waterfall_results"),
    path("projects/<int:project_id>/tranches/add/", views.add_tranche, name="add_tranche"),
    path("projects/<int:project_id>/tranches/<int:tranche_id>/edit/", views.edit_tranche, name="edit_tranche"),
    path("projects/<int:project_id>/tranches/<int:tranche_id>/delete/", views.delete_tranche, name="delete_tranche"),
    path("projects/<int:project_id>/tranches/<int:tranche_id>/claims/add/", views.add_claim, name="add_claim"),
    path("projects/<int:project_id>/tranches/<int:tranche_id>/claims/<int:claim_id>/edit/", views.edit_claim, name="edit_claim"),
    path("projects/<int:project_id>/tranches/<int:tranche_id>/claims/<int:claim_id>/delete/", views.delete_claim, name="delete_claim"),
    path("projects/<int:project_id>/lines/add/", views.add_budget_line, name="add_budget_line"),
    path("projects/<int:project_id>/lines/<int:line_id>/edit/", views.edit_budget_line, name="edit_budget_line"),
    path("projects/<int:project_id>/lines/<int:line_id>/delete/", views.delete_budget_line, name="delete_budget_line"),
]
