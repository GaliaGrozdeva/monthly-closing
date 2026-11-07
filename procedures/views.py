from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from categories.models import Category
from .forms import ProcedureDeleteForm, ProcedureForm
from .models import Procedure


@require_GET
def procedure_list(request):
    procedures = Procedure.objects.select_related("category")
    return render(request, "procedures/list.html", {"procedures": procedures})


@require_GET
def procedure_detail(request, pk):
    procedure = get_object_or_404(Procedure.objects.select_related("category"), pk=pk)
    return render(request, "procedures/detail.html", {"procedure": procedure})


@require_http_methods(["GET", "POST"])
def procedure_create(request):
    initial = {}
    if request.method == "GET" and "category" in request.GET:
        try:
            category_id = int(request.GET["category"])
        except (ValueError, TypeError):
            raise Http404("Категорията не е намерена.")
        initial["category"] = get_object_or_404(Category, pk=category_id)
    form = ProcedureForm(request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        procedure = form.save()
        messages.success(request, "Процедурата е създадена.")
        return redirect(procedure)
    return render(request, "procedures/create.html", {"form": form, "has_categories": Category.objects.exists()})


@require_http_methods(["GET", "POST"])
def procedure_edit(request, pk):
    procedure = get_object_or_404(Procedure, pk=pk)
    form = ProcedureForm(request.POST if request.method == "POST" else None, instance=procedure)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Промените са запазени.")
        return redirect(procedure)
    return render(request, "procedures/edit.html", {"form": form, "procedure": procedure})


@require_http_methods(["GET", "POST"])
def procedure_delete(request, pk):
    procedure = get_object_or_404(Procedure, pk=pk)
    form = ProcedureDeleteForm(
        request.POST if request.method == "POST" else None, initial={"title": procedure.title},
    )
    if request.method == "POST" and form.is_valid():
        category = procedure.category
        procedure.delete()
        messages.success(request, "Процедурата е изтрита.")
        return redirect(category)
    return render(request, "procedures/delete.html", {"form": form, "procedure": procedure})
