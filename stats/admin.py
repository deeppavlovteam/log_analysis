from django.contrib import admin

from .models import Record, Hash, File, Config
from django.db.models import Count, Q
from django.contrib.admin import SimpleListFilter
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter


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


class MyDateFilter(DateRangeFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super(MyDateFilter, self).__init__('asdf', request, params, model, model_admin, 'time')

    def queryset(self, request, queryset):
        return queryset


class RecordAdmin(admin.ModelAdmin):
    list_display = ('ip', 'file', 'config', 'outer_request')
#    fields = ['file', 'time']
    list_filter = ['outer_request']
    search_fields = ['file__name']
#    search_fields = ['ip', 'config']


class FileAdmin(admin.ModelAdmin):
    list_display = ('name', 'n_records')
    search_fields = ['name']
    list_filter = (ResponseCodeFilter, OuterRequestFilter, 'md5', ('name', MyDateFilter))

    def get_queryset(self, request):
        qs = super(admin.ModelAdmin, self).get_queryset(request)

        default_filter = Q()
        for filter in self.list_filter:
            print(request.GET)
            if isinstance(filter, str):
                continue
            elif isinstance(filter, tuple):
                gte = request.GET.get('time__range__gte')
                lte = request.GET.get('time__range__lte')
                dic = {}
                if gte is not None:
                    dic.update({'record__time__gte': gte})
                if lte is not None:
                    dic.update({'record__time__lte': lte})
                if dic:
                    default_filter &= Q(**dic)
            else:
                val = request.GET.get(filter.parameter_name)
                if val is not None:
                    default_filter &= Q(**{f'record__{filter.parameter_name}': val})

        return qs.annotate(n_records=Count('record', filter=default_filter))

    def n_records(self, inst):
        return inst.n_records

    n_records.admin_order_field = 'n_records'


admin.site.register(Record, RecordAdmin)
admin.site.register(Hash)
admin.site.register(File, FileAdmin)
admin.site.register(Config)