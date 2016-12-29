from django.contrib import admin
# from .models import Primer, Barcode
from .models import Experiment
from pm.models import Sample


class PrimerAdmin(admin.ModelAdmin):
    """
    Admin class for primer
    """
    list_display = ('name', 'forward_primer', 'reverse_primer')


class BarcodeAdmin(admin.ModelAdmin):
    """
    Admin class for Barcode
    """
    list_display = ('name', 'sequence')


class ExperimentAdmin(admin.ModelAdmin):
    """
    Admin class for experiment
    """
    list_display = ('sample_project_contract_number', 'sample_project_name', 'sample', 'status')
    list_display_links = None
    readonly_fields = ['sample']
    actions = ['make_wai', 'make_ext', 'make_qc', 'make_lib', 'delete_selected']
    list_filter = ['status', 'sample__project__name', 'sample__project__contract_number']

    def sample_project_contract_number(self, obj):
        return obj.sample.project.contract_number
    sample_project_contract_number.short_description = '合同号'

    def sample_project_name(self, obj):
        return obj.sample.project.name
    sample_project_name.short_description = '项目名'

    def make_wai(self, request, queryset):
        """
        批量更改状态为等待实验
        :param request:
        :param queryset:
        :return:
        """
        rows_updated = queryset.update(status='WAI')
        self.message_user(request, '%s 个样品已成功更新状态为等待实验' % rows_updated)
    make_wai.short_description = '更新状态为 等待实验'

    def make_ext(self, request, queryset):
        """
        批量更改状态为提取完成
        :param request:
        :param queryset:
        :return:
        """
        rows_updated = queryset.update(status='EXT')
        self.message_user(request, '%s 个样品已成功更新状态为提取完成' % rows_updated)
    make_ext.short_description = '更新状态为 提取完成'

    def make_qc(self, request, queryset):
        """
        批量更改状态为质控完成
        :param request:
        :param queryset:
        :return:
        """
        rows_updated = queryset.update(status='QC')
        self.message_user(request, '%s 个样品已成功更新状态为质控完成' % rows_updated)
    make_qc.short_description = '更新状态为 质控完成'

    def make_lib(self, request, queryset):
        """
        批量更改状态为建库完成
        :param request:
        :param queryset:
        :return:
        """
        rows_updated = queryset.update(status='LIB')
        self.message_user(request, '%s 个样品已成功更新状态为建库完成' % rows_updated)
    make_lib.short_description = '更新状态为 建库完成'

    def delete_selected(self, request, obj):
        for o in obj.all():
            o.sample.experiment_num -= 1
            o.sample.save()
            o.delete()

    delete_selected.short_description = '将样品退回至项目管理'

# admin.site.register(Primer, PrimerAdmin)
# admin.site.register(Barcode, BarcodeAdmin)
admin.site.register(Experiment, ExperimentAdmin)