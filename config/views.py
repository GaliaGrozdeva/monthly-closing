from django.shortcuts import render
from django.views.decorators.http import require_GET

from categories.models import Category


@require_GET
def home(request):
    return render(request, "home.html", {"categories": Category.objects.all()})


@require_GET
def about(request):
    return render(request, "about.html")
