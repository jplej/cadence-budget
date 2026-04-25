from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get("next", "dashboard"))
        messages.error(request, _("Invalid email or password."))
    return render(request, "users/login.html", {"title": _("Sign In")})


def logout_view(request):
    logout(request)
    return redirect("landing")


@login_required
def dashboard(request):
    return render(request, "core/dashboard.html", {"title": _("Dashboard")})
