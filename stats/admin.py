from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Count, Q, OuterRef
from django.db.models.functions import Coalesce
from rangefilter.filter import DateRangeFilter

from .models import Record, Hash, File, Config, ConfigName


class ResponseCodeFilter(SimpleListFilter):
    title = 'response_code'
    parameter_name = 'response_code'

    def lookups(self, request, model_admin):
        return (
            (200, '200'),
        )

    def queryset(self, request, queryset):
        return queryset


class OuterRequestFilter(SimpleListFilter):
    title = 'request type'
    parameter_name = 'outer_request'

    def lookups(self, request, model_admin):
        return (
            (True, 'Outer'),
        )

    def queryset(self, request, queryset):
        return queryset


class FileInConfigFilter(SimpleListFilter):
    title = 'file in configs'
    # !!! ТУТ здоровенный костыль: назвал параметр 'ip' чтобы он проходил проверку, но при этом это название параметра
    # заставляет фильтровать records по ip. Чтобы этого не было, в getqueryset FileAdmin была добавлена проверка на
    # имя параметра
    parameter_name = 'ip'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'DeepPavlov library'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(pk__in=list(Config.objects.values_list('files', flat=True).distinct()))
        return queryset


class MyDateFilter(DateRangeFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super(MyDateFilter, self).__init__('asdf', request, params, model, model_admin, 'time')

    def queryset(self, request, queryset):
        return queryset


class RecordAdmin(admin.ModelAdmin):
    list_display = ('ip', 'file', 'config', 'outer_request', 'response_code', 'time')
#    fields = ['file', 'time']
    list_filter = ['outer_request', 'response_code']
    search_fields = ['file__name', 'config__name']
#    search_fields = ['ip', 'config']
    def has_delete_permission(self, request, obj=None):
        return False


class ConfigNameAdmin(admin.ModelAdmin):
    list_display = ('name',)

    def has_delete_permission(self, request, obj=None):
        return False


class ConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'dp_version', 'n_downloads', 'files_display')
    list_filter = [('type', MyDateFilter), ResponseCodeFilter, OuterRequestFilter, 'dp_version', 'type']

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super(admin.ModelAdmin, self).get_queryset(request)
        sub = Record.objects.filter(config=OuterRef('name'))
        for filter in self.list_filter:
            if isinstance(filter, str):
                continue
            elif isinstance(filter, tuple):
                gte = request.GET.get('time__range__gte')
                lte = request.GET.get('time__range__lte')
                dic = {}
                if gte is not None and gte != '':
                    dic.update({'time__gte': gte})
                if lte is not None and lte != '':
                    dic.update({'time__lte': lte})
                if dic:
                    sub = sub.filter(**dic)
            else:
                val = request.GET.get(filter.parameter_name)
                if val is not None:
                    sub = sub.filter(**{f'{filter.parameter_name}': val})
        sub = sub.values('file').annotate(x=Count('file')).order_by('-x').values('x')[:1]
        return qs.annotate(n_downloads=Coalesce(sub, 0))

    def n_downloads(self, inst):
        return inst.n_downloads
    n_downloads.admin_order_field = 'n_downloads'


class FileAdmin(admin.ModelAdmin):
    list_display = ('name', 'n_records', 'configs')
    search_fields = ['name']
    list_filter = (FileInConfigFilter, ResponseCodeFilter, OuterRequestFilter, 'md5', ('name', MyDateFilter))

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super(admin.ModelAdmin, self).get_queryset(request)

        default_filter = Q()
        for filter in self.list_filter:
            if isinstance(filter, str):
                continue
            elif isinstance(filter, tuple):
                gte = request.GET.get('time__range__gte')
                lte = request.GET.get('time__range__lte')
                dic = {}
                if gte is not None and gte != '':
                    dic.update({'record__time__gte': gte})
                if lte is not None and lte != '':
                    dic.update({'record__time__lte': lte})
                if dic:
                    default_filter &= Q(**dic)
            else:
                val = request.GET.get(filter.parameter_name)
                if val is not None and filter.parameter_name != 'ip':
                    default_filter &= Q(**{f'record__{filter.parameter_name}': val})

        return qs.annotate(n_records=Count('record', filter=default_filter))

    def n_records(self, inst):
        return inst.n_records

    n_records.admin_order_field = 'n_records'


admin.site.register(Record, RecordAdmin)
admin.site.register(Hash)
admin.site.register(File, FileAdmin)
admin.site.register(Config, ConfigAdmin)
admin.site.register(ConfigName, ConfigNameAdmin)
