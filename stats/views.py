from django.http import Http404
from django.shortcuts import render
from django.views import generic

from .models import Record


class IndexView(generic.ListView):
    paginate_by = 2
    template_name = 'stats/index.html'
    context_object_name = 'latest_records'

    def get_queryset(self):
        """Return the last five published questions."""
        return Record.objects.order_by('-time')[:5]


class DetailView(generic.DetailView):
    model = Record
    template_name = 'stats/detail.html'
