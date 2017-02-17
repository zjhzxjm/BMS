from django.contrib import admin
from .models import SampleInfo, QcTask, ExtTask, LibTask
from django.contrib import messages


class SampleInfoAdmin(admin.ModelAdmin):
    list_display = ['project', 'type', 'species', 'name', 'volume', 'concentration', 'is_qc', 'is_ext', 'is_lib',
                    'receive_date', 'check']
    list_editable = ['is_qc', 'is_ext', 'is_lib']


class QcTaskAdmin(admin.ModelAdmin):
    list_display = ['sample', 'date', 'staff', 'volume', 'concentration', 'total', 'result']


class ExtTaskAdmin(admin.ModelAdmin):
    list_display = ['sample', 'date', 'result']


class LibTaskAdmin(admin.ModelAdmin):
    list_display = ['sample', 'date', 'staff', 'type', 'sample_code', 'lib_code', 'index', 'length', 'volume',
                    'concentration', 'total', 'result']

admin.site.register(SampleInfo, SampleInfoAdmin)
admin.site.register(QcTask, QcTaskAdmin)
admin.site.register(ExtTask, ExtTaskAdmin)
admin.site.register(LibTask, LibTaskAdmin)
