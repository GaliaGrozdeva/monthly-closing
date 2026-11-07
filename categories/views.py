from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import CategoryDeleteForm, CategoryForm
from .models import Category


@require_GET
def category_list(request):
    return render(request, "categories/list.html", {"categories": Category.objects.all()})


@require_GET
def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    return render(request, "categories/detail.html", {
        "category": category, "procedures": category.procedures.all(),
    })


@require_http_methods(["GET", "POST"])
def category_create(request):
    form = CategoryForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        category = form.save()
        messages.success(request, "Категорията е създадена.")
        return redirect(category)
    return render(request, "categories/create.html", {"form": form})


@require_http_methods(["GET", "POST"])
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST if request.method == "POST" else None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Промените са запазени.")
        return redirect(category)
    return render(request, "categories/edit.html", {"form": form, "category": category})


@require_http_methods(["GET", "POST"])
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryDeleteForm(
        request.POST if request.method == "POST" else None,
        initial={"name": category.name},
    )
    if request.method == "POST" and form.is_valid():
        try:
            category.delete()
        except ProtectedError:
            form.add_error(None, "Категорията съдържа процедури. Премести ги в друга категория или ги изтрий, преди да изтриеш категорията.")
        else:
            messages.success(request, "Категорията е изтрита.")
            return redirect("categories:list")
    return render(request, "categories/delete.html", {"form": form, "category": category})
