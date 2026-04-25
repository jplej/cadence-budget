from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


def landing(request):
    return render(request, "tenants/landing.html", {"title": _("Welcome")})
