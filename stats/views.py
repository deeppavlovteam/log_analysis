from django.http import Http404
from django.shortcuts import render

from .models import Record


def index(request):
    latest_records = Record.objects.order_by('-time')[:5]
    context = {'latest_records': latest_records}
    return render(request, 'stats/index.html', context)


def detail(request, id):
    try:
        record = Record.objects.get(id=id)
    except Record.DoesNotExist:
        raise Http404("Record does not exist")
    return render(request, 'stats/detail.html', {'record': record})
