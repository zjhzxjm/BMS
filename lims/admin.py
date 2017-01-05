from django.contrib import admin
# from .models import Primer, Barcode
from .models import Experiment
from pm.models import Sample
from django.contrib import messages


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
    # list_display = ('sample_project_contract_number', 'sample_project_name', 'sample', 'status')
    # list_display_links = None
    # readonly_fields = ['sample']
    # actions = ['make_wai', 'make_ext', 'make_qc', 'make_lib', 'delete_selected']
    # list_filter = ['status', 'sample__project__name', 'sample__project__contract_number']

    def sample_project_contract_number(self, obj):
        return obj.sample.project.contract.contract_number
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
        n = obj.all().count()
        w = obj.filter(status='WAI').count()
        d = ''
        for o in obj.filter(status='WAI'):
            o.sample.experiment_num -= 1
            o.sample.save()
            d = o.delete()
        if d and n == w:
            self.message_user(request, '%s 个样品已成功退回到项目管理' % n)
        else:
            self.message_user(request, '有 %s 个样品需变更状态为等待实验才能退回' % (n-w), level=messages.WARNING)
    delete_selected.short_description = '将样品退回至项目管理'

    def get_queryset(self, request):
        # 只允许管理员和拥有该模型删除权限的人员才能查看所有样品
        qs = super(ExperimentAdmin, self).get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('lims.delete_experiment') or \
            request.user.has_perm('pm.delete_sample'):
            return qs
        return qs.filter(sample__project__customer__linker=request.user)

    def get_actions(self, request):
        # 无权限人员取消actions
        actions = super(ExperimentAdmin, self).get_actions(request)
        if not request.user.has_perm('lims.delete_experiment'):
            actions = None
        return actions

# admin.site.register(Primer, PrimerAdmin)
# admin.site.register(Barcode, BarcodeAdmin)
admin.site.register(Experiment, ExperimentAdmin)