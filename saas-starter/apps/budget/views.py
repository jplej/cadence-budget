from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import Partner


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
