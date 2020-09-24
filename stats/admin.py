from django.contrib import admin

from .models import Record, Hash, File, Config
from django.db.models import Count, Q


class RecordAdmin(admin.ModelAdmin):
    list_display = ('ip', 'file', 'config', 'outer_request')
#    fields = ['file', 'time']
    list_filter = ['outer_request']
#    search_fields = ['ip', 'config']


class FileAdmin(admin.ModelAdmin):
    list_display = ('name', 'foo', 'foo1')
    search_fields = ['name']
    def get_queryset(self, request):
        qs = super(admin.ModelAdmin, self).get_queryset(request)
        return qs.annotate(foo1=Count('record', filter=Q(record__response_code=200)))
    def foo1(self, inst):
        return inst.foo1
    foo1.admin_order_field = 'foo1'


admin.site.register(Record, RecordAdmin)
admin.site.register(Hash)
admin.site.register(File, FileAdmin)
admin.site.register(Config)