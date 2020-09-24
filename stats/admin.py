from django.contrib import admin

from .models import Record, Hash, File, Config
from django.db.models import Count, Q
from django.contrib.admin import SimpleListFilter


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



class RecordAdmin(admin.ModelAdmin):
    list_display = ('ip', 'file', 'config', 'outer_request')
#    fields = ['file', 'time']
    list_filter = ['outer_request']
    search_fields = ['file__name']
#    search_fields = ['ip', 'config']


class FileAdmin(admin.ModelAdmin):
    list_display = ('name', 'foo', 'foo1')
    search_fields = ['name']
    list_filter = (ResponseCodeFilter, OuterRequestFilter)
    def get_queryset(self, request):
        qs = super(admin.ModelAdmin, self).get_queryset(request)

        default_filter = Q()
        for filter in self.list_filter:
            val = request.GET.get(filter.parameter_name)
            if val is not None:
                default_filter &= Q(**{f'record__{filter.parameter_name}': val})

        return qs.annotate(foo1=Count('record', filter=default_filter))
    def foo1(self, inst):
        return inst.foo1
    foo1.admin_order_field = 'foo1'


admin.site.register(Record, RecordAdmin)
admin.site.register(Hash)
admin.site.register(File, FileAdmin)
admin.site.register(Config)