from django.contrib import admin

from .models import Record, Hash, File, Config


class RecordAdmin(admin.ModelAdmin):
    list_display = ('ip', 'file', 'config', 'outer_request')
#    fields = ['file', 'time']
    list_filter = ['outer_request']
#    search_fields = ['ip', 'config']

admin.site.register(Record, RecordAdmin)
admin.site.register(Hash)
admin.site.register(File)
admin.site.register(Config)