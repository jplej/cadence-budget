from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import Category, Partner, Project, ProjectTag


def _require_tenant(request):
    if request.tenant is None:
        raise Http404


def _partner_fields_from_post(post):
    return {
        "name": post.get("name", "").strip(),
        "is_internal": post.get("is_internal") == "on",
        "contact_name": post.get("contact_name", "").strip(),
        "contact_email": post.get("contact_email", "").strip(),
        "contact_phone": post.get("contact_phone", "").strip(),
    }


@login_required
def list_partners(request):
    _require_tenant(request)
    partners = Partner.objects.filter(tenant=request.tenant)
    error = None
    edit_partner_id = None
    edit_error = None

    if request.method == "POST":
        fields = _partner_fields_from_post(request.POST)
        if not fields["name"]:
            error = _("Name is required.")
        else:
            Partner.objects.create(tenant=request.tenant, **fields)
            return redirect("list_partners")

    try:
        edit_partner_id = int(request.GET.get("edit", ""))
    except (ValueError, TypeError):
        pass
    edit_error = request.GET.get("error_edit", "")

    return render(request, "budget/partners.html", {
        "title": _("Partners"),
        "partners": partners,
        "error": error,
        "edit_partner_id": edit_partner_id,
        "edit_error": edit_error,
    })


@login_required
def edit_partner(request, partner_id):
    _require_tenant(request)
    partner = get_object_or_404(Partner, id=partner_id, tenant=request.tenant)

    if request.method == "POST":
        fields = _partner_fields_from_post(request.POST)
        if not fields["name"]:
            params = urlencode({"edit": partner_id, "error_edit": str(_("Name is required."))})
            return redirect(f"{reverse('list_partners')}?{params}")
        for attr, value in fields.items():
            setattr(partner, attr, value)
        partner.save()
    return redirect("list_partners")


@login_required
def delete_partner(request, partner_id):
    _require_tenant(request)
    partner = get_object_or_404(Partner, id=partner_id, tenant=request.tenant)
    if request.method == "POST":
        partner.delete()
    return redirect("list_partners")


def _category_fields_from_post(post, tenant):
    parent_id = post.get("parent_id", "").strip()
    parent = None
    if parent_id:
        try:
            parent = Category.objects.get(id=int(parent_id), tenant=tenant, parent=None)
        except (Category.DoesNotExist, ValueError):
            pass
    return {
        "name": post.get("name", "").strip(),
        "code": post.get("code", "").strip(),
        "parent": parent,
    }


@login_required
def list_categories(request):
    _require_tenant(request)
    categories = Category.objects.filter(tenant=request.tenant).select_related("parent")
    top_level = Category.objects.filter(tenant=request.tenant, parent=None)
    error = None
    edit_category_id = None
    edit_error = None

    if request.method == "POST":
        fields = _category_fields_from_post(request.POST, request.tenant)
        if not fields["name"]:
            error = _("Name is required.")
        else:
            Category.objects.create(tenant=request.tenant, **fields)
            return redirect("list_categories")

    try:
        edit_category_id = int(request.GET.get("edit", ""))
    except (ValueError, TypeError):
        pass
    edit_error = request.GET.get("error_edit", "")

    return render(request, "budget/categories.html", {
        "title": _("Categories"),
        "categories": categories,
        "top_level": top_level,
        "error": error,
        "edit_category_id": edit_category_id,
        "edit_error": edit_error,
    })


@login_required
def edit_category(request, category_id):
    _require_tenant(request)
    category = get_object_or_404(Category, id=category_id, tenant=request.tenant)

    if request.method == "POST":
        fields = _category_fields_from_post(request.POST, request.tenant)
        if not fields["name"]:
            params = urlencode({"edit": category_id, "error_edit": str(_("Name is required."))})
            return redirect(f"{reverse('list_categories')}?{params}")
        # prevent a category from becoming its own parent
        if fields["parent"] and fields["parent"].id == category.id:
            fields["parent"] = None
        for attr, value in fields.items():
            setattr(category, attr, value)
        category.save()
    return redirect("list_categories")


@login_required
def delete_category(request, category_id):
    _require_tenant(request)
    category = get_object_or_404(Category, id=category_id, tenant=request.tenant)
    if request.method == "POST":
        category.delete()
    return redirect("list_categories")


def _tags_from_input(raw):
    """Parse comma/space separated tag input into cleaned ltree-safe strings."""
    tags = []
    for token in raw.replace(",", " ").split():
        token = token.strip().lower().replace(" ", "_")
        if token:
            tags.append(token)
    return tags


@login_required
def list_projects(request):
    _require_tenant(request)
    projects = Project.objects.filter(tenant=request.tenant).prefetch_related("tags")
    return render(request, "budget/projects.html", {
        "title": _("Projects"),
        "projects": projects,
    })


@login_required
def edit_project(request, project_id=None):
    _require_tenant(request)
    project = None
    if project_id:
        project = get_object_or_404(Project, id=project_id, tenant=request.tenant)

    error = None
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        tags_raw = request.POST.get("tags", "")
        if not name:
            error = _("Name is required.")
        else:
            if project is None:
                project = Project.objects.create(
                    tenant=request.tenant, name=name, description=description
                )
            else:
                project.name = name
                project.description = description
                project.save()

            project.tags.all().delete()
            for tag in _tags_from_input(tags_raw):
                ProjectTag.objects.create(project=project, tag=tag)

            return redirect("list_projects")

    tags_value = ", ".join(t.tag.replace(".", "/") for t in project.tags.all()) if project else ""
    return render(request, "budget/project_form.html", {
        "title": _("Edit Project") if project else _("New Project"),
        "project": project,
        "tags_value": tags_value,
        "error": error,
    })


@login_required
def delete_project(request, project_id):
    _require_tenant(request)
    project = get_object_or_404(Project, id=project_id, tenant=request.tenant)
    if request.method == "POST":
        project.delete()
    return redirect("list_projects")
