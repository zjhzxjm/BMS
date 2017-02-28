from django.contrib import admin
from .models import SampleInfo, QcTask, ExtTask, LibTask
from django.contrib import messages
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class SampleInfoResource(resources.ModelResource):
    class Meta:
        model = SampleInfo
        exclude = ('receive_date', 'check', 'note')
        skip_unchanged = True


class SampleInfoAdmin(ImportExportModelAdmin):
    list_display = ['contract', 'project', 'type', 'species', 'name', 'volume', 'concentration', 'receive_date', 'check']
    resources_class = SampleInfoResource
    list_display_links = ['name']

    def contract(self, obj):
        return obj.project.contract
    contract.short_description = '合同'


class ExtTaskAdmin(admin.ModelAdmin):
    list_display = ['sample', 'date', 'result']


class QcTaskAdmin(admin.ModelAdmin):
    list_display = ['sample', 'date', 'staff', 'volume', 'concentration', 'total', 'result']


class LibTaskAdmin(admin.ModelAdmin):
    list_display = ['sample', 'date', 'staff', 'type', 'sample_code', 'lib_code', 'index', 'length', 'volume',
                    'concentration', 'total', 'result']

admin.site.register(SampleInfo, SampleInfoAdmin)
admin.site.register(ExtTask, ExtTaskAdmin)
admin.site.register(QcTask, QcTaskAdmin)
admin.site.register(LibTask, LibTaskAdmin)
