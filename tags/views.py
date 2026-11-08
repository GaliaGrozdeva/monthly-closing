from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import TagDeleteForm, TagForm
from .models import Tag


@require_GET
def tag_list(request):
    tags = Tag.objects.annotate(procedure_count=Count("procedures"))
    return render(request, "tags/list.html", {"tags": tags})


@require_GET
def tag_detail(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    procedures = tag.procedures.select_related("category")
    return render(request, "tags/detail.html", {"tag": tag, "procedures": procedures})


@require_http_methods(["GET", "POST"])
def tag_create(request):
    form = TagForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        tag = form.save()
        messages.success(request, "Етикетът е създаден.")
        return redirect(tag)
    return render(request, "tags/create.html", {"form": form})


@require_http_methods(["GET", "POST"])
def tag_edit(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    form = TagForm(request.POST if request.method == "POST" else None, instance=tag)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Промените са запазени.")
        return redirect(tag)
    return render(request, "tags/edit.html", {"form": form, "tag": tag})


@require_http_methods(["GET", "POST"])
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    form = TagDeleteForm(
        request.POST if request.method == "POST" else None,
        initial={"name": tag.name},
    )
    if request.method == "POST" and form.is_valid():
        tag.delete()
        messages.success(request, "Етикетът е изтрит.")
        return redirect("tags:list")
    return render(request, "tags/delete.html", {
        "form": form, "tag": tag, "procedure_count": tag.procedures.count(),
    })
