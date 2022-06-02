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

        country_stat = records.values('ip__country').annotate(total=Count('ip__country')).filter(total__gt=0).values('ip__country', 'total').order_by('-total')
        country_count = [v['total'] for v in country_stat]
        country_count = [c / sum(country_count) for c in country_count]
        context['countries'] = [str(k['ip__country']) for k in country_stat]  # to prevent chart error in case if ip country is None
        context['country_count'] = country_count

        return context
