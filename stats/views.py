from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.views import generic
from django.views.generic import TemplateView

from .models import Record, Config


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


class StatsChartView(TemplateView):
    template_name = 'stats/chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config_id = kwargs.pop('config_id')
        conf = Config.objects.get(id=config_id)
        records = Record.objects.filter(config=conf.name).filter(response_code=200)

        week_ip = records.values(week=TruncWeek('time')).annotate(total=Count('ip', distinct=True)).order_by('week')
        context["week_ips_count"] = [w['total'] for w in week_ip]
        context["week_ips_labels"] = [w['week'].strftime('%d%m%y') for w in week_ip]

        try:
            most_popular_file_id = records.values('file').annotate(total=Count('file')).order_by('-total')[0]['file']
            week_record = records.filter(file=most_popular_file_id).values(week=TruncWeek('time')).annotate(total=Count('file')).order_by('week')

            context["week_records_count"] = [w['total'] for w in week_record]
            context["week_records_labels"] = [w['week'].strftime('%d%m%y') for w in week_record]
        except IndexError:
            context["week_records_count"] = context["week_records_labels"] = []
        return context
