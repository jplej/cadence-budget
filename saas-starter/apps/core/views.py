from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _


def index(request):
    return render(request, "core/index.html", {"title": _("Home")})
