from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


def index(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    else:
        return redirect("login")


@login_required
def dashboard(request):
    return render(request, "analyst/dashboard.html")
