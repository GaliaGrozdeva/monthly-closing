from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from categories.models import Category
from .forms import ProcedureDeleteForm, ProcedureFilterForm, ProcedureForm
from .models import Procedure


@require_GET
def procedure_list(request):
    filter_form = ProcedureFilterForm(request.GET)
    queryset = Procedure.objects.select_related("category").prefetch_related("tags")
    procedures = []
    selected_category = None
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        selected_category = data["category"]
        if selected_category:
            queryset = queryset.filter(category=selected_category)
        if data["tag"]:
            queryset = queryset.filter(tags=data["tag"])

        # casefold разпознава главни и малки букви и на кирилица.
        words = data["q"].casefold().split()
        for procedure in queryset:
            text = (procedure.title + "\n" + procedure.steps).casefold()
            if all(word in text for word in words):
                procedures.append(procedure)

        if data["sort"] == "newest":
            procedures.sort(key=lambda item: item.pk, reverse=True)
        elif data["sort"] == "category":
            procedures.sort(key=lambda item: (item.category.name.casefold(), item.title.casefold(), item.pk))
        else:
            procedures.sort(key=lambda item: (item.title.casefold(), item.pk), reverse=data["sort"] == "title_desc")

    return render(request, "procedures/list.html", {
        "procedures": procedures,
        "filter_form": filter_form,
        "filter_query": filter_form.get_query_string(),
        "selected_category": selected_category,
        "total_count": Procedure.objects.count(),
    })


@require_GET
def procedure_detail(request, pk):
    procedure = get_object_or_404(Procedure.objects.select_related("category").prefetch_related("tags"), pk=pk)
    filter_query = ""
    if any(key in request.GET for key in ProcedureFilterForm.base_fields):
        filter_query = ProcedureFilterForm(request.GET).get_query_string()
    return render(request, "procedures/detail.html", {
        "procedure": procedure, "filter_query": filter_query,
    })


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
