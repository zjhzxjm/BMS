from django.contrib import admin
from .models import Project, QcSubmit, ExtSubmit, LibSubmit
from lims.models import SampleInfo, QcTask, ExtTask, LibTask
from django import forms
from datetime import date, timedelta
from fm.models import Bill
from mm.models import Contract
from django.db.models import Sum
from django.utils.html import format_html


def add_business_days(from_date, number_of_days):
    to_date = from_date
    while number_of_days:
        to_date += timedelta(1)
        if to_date.weekday() < 5:
            number_of_days -= 1
    return to_date


def is_period_income(contract, period):
    income = Bill.objects.filter(invoice__invoice__contract=contract).filter(invoice__invoice__period=period)\
            .aggregate(total_income=Sum('income'))['total_income'] or 0
    if period == 'FIS':
        amount = Contract.objects.filter(contract_number=contract)[0].fis_amount
    elif period == 'FIN':
        amount = Contract.objects.filter(contract_number=contract)[0].fin_amount
    return amount - income


class StatusListFilter(admin.SimpleListFilter):
    title = '项目状态'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('FIS', '待首款'),
            ('ENS', '待确认'),
            ('QC', '质检中'),
            ('EXT', '提取中'),
            ('LIB', '建库中'),
            ('SEQ', '测序中'),
            ('ANA', '分析中'),
            ('FIN', '待尾款'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'FIS':
            return queryset.filter(contract__fis_date=None)
        if self.value() == 'ENS':
            return queryset.exclude(contract__fis_date=None).filter(is_confirm=False)
        if self.value() == 'QC':
            return queryset.filter(is_confirm=True).filter(qc_date=None)
        if self.value() == 'EXT':
            return queryset.filter(is_confirm=True).exclude(qc_date=None).filter(ext_date=None)
        if self.value() == 'LIB':
            return queryset.filter(is_confirm=True).exclude(qc_date=None).exclude(ext_date=None).filter(lib_date=None)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('contract', 'customer', 'name', 'is_confirm', 'status', 'sample_num',
                    'receive_date', 'contract_node', 'ext_status', 'qc_status', 'lib_status')
    list_editable = ['is_confirm']
    list_filter = [StatusListFilter]
    fieldsets = (
        ('合同信息', {
           'fields': (('contract', 'contract_name'),)
        }),
        ('项目信息', {
            'fields': ('customer', 'name', 'service_type', 'data_amount')
        }),
        ('周期设置(工作日)', {
           'fields': (('ext_cycle', 'qc_cycle', 'lib_cycle', 'ana_cycle'),)
        }),
    )
    readonly_fields = ['contract_name']
    raw_id_fields = ['contract']

    def contract_name(self, obj):
        return obj.contract.name
    contract_name.short_description = '项目名称'

    def status(self, obj):
        if is_period_income(obj.contract, 'FIS') > 0:
            return '待首款'
        if obj.lib_date:
            return '测序中'
        if LibTask.objects.filter(sample__project=obj).count():
            return '建库中'
        if ExtTask.objects.filter(sample__project=obj).count():
            return '提取中'
        if QcTask.objects.filter(sample__project=obj).count():
            return '质检中'
        if is_period_income(obj.contract, 'FIS') == 0:
            return '待确认'
        return 1
    status.short_description = '状态'

    def sample_num(self, obj):
        return SampleInfo.objects.filter(project=obj).count()
    sample_num.short_description = '实际收样'

    def receive_date(self, obj):
        qs_sample = SampleInfo.objects.filter(project=obj)
        if qs_sample:
            return qs_sample.last().receive_date.strftime('%Y-%m-%d')
    receive_date.short_description = '收样时间'

    def contract_node(self, obj):
        if obj.due_date:
            return obj.due_date.strftime('%Y-%m-%d')
        else:
            return
    contract_node.short_description = '合同节点'

    def ext_status(self, obj):
        if not obj.due_date:
            return '-'
        total = ExtTask.objects.filter(sample__project=obj).count()
        done = ExtTask.objects.filter(sample__project=obj).exclude(result=None).count()
        if done != total or not total:
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.lib_cycle + obj.qc_cycle) - date.today()).days
            if left >= 0:
                return '%s/%s-余%s天' % (done, total, left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s/%s-延%s天' % (done, total, -left))
        else:
            obj.ext_date = ExtTask.objects.filter(sample__project=obj).order_by('-date').first().date
            obj.save()
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.lib_cycle + obj.qc_cycle) - obj.ext_date).days
            if left >= 0:
                return '%s-提前%s天' % (obj.ext_date, left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天' % (obj.ext_date, -left))
    ext_status.short_description = '提取进度'

    def qc_status(self, obj):
        if not obj.due_date:
            return '-'
        total = QcTask.objects.filter(sample__project=obj).count()
        done = QcTask.objects.filter(sample__project=obj).exclude(result=None).count()
        if done != total or not total:
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.lib_cycle) - date.today()).days
            if left >= 0:
                return '%s/%s-余%s天' % (done, total, left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s/%s-延%s天' % (done, total, -left))
        else:
            obj.qc_date = QcTask.objects.filter(sample__project=obj).order_by('-date').first().date
            obj.save()
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.lib_cycle) - obj.qc_date).days
            if left >= 0:
                return '%s-提前%s天' % (obj.qc_date, left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天' % (obj.qc_date, -left))
    qc_status.short_description = '质检进度'

    def lib_status(self, obj):
        if not obj.due_date:
            return '-'
        total = LibTask.objects.filter(sample__project=obj).count()
        done = LibTask.objects.filter(sample__project=obj).exclude(result=None).count()
        if done != total or not total:
            left = (obj.due_date - timedelta(obj.ana_cycle) - date.today()).days
            if left >= 0:
                return '%s/%s-余%s天' % (done, total, left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s/%s-延%s天' % (done, total, -left))
        else:
            obj.lib_date = LibTask.objects.filter(sample__project=obj).order_by('-date').first().date
            obj.save()
            left = (obj.due_date - timedelta(obj.ana_cycle) - obj.lib_date).days
            if left >= 0:
                return '%s-提前%s天' % (obj.lib_date, left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天' % (obj.lib_date, -left))
    lib_status.short_description = '建库进度'

    def get_queryset(self, request):
        # 只允许管理员和拥有该模型新增权限的人员才能查看所有样品
        qs = super(ProjectAdmin, self).get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('pm.add_project'):
            return qs
        return qs.filter(contract__salesman=request.user)

    def get_actions(self, request):
        # 无权限人员取消actions
        actions = super(ProjectAdmin, self).get_actions(request)
        if not request.user.has_perm('pm.delete_project'):
            actions = None
        return actions


class ExtSubmitForm(forms.ModelForm):
    # 已经提取成功或正在提取的样品不显示
    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        if 'sample' in self.fields:
            values = ExtTask.objects.exclude(result=False).values_list('sample__pk', flat=True)
            self.fields['sample'].queryset = SampleInfo.is_ext_objects.exclude(id__in=list(set(values)))

    def clean(self):
        self.instance.__sample__ = self.cleaned_data['sample']


class ExtSubmitAdmin(admin.ModelAdmin):
    form = ExtSubmitForm
    list_display = ['slug', 'contract_count', 'project_count', 'sample_count', 'date', 'is_submit']
    filter_horizontal = ('sample',)
    fields = ('slug', 'date', 'sample', 'is_submit')

    def contract_count(self, obj):
        return len(set(i.project.contract.contract_number for i in obj.sample.all()))
    contract_count.short_description = '合同数'

    def project_count(self, obj):
        return len(set([i.project.name for i in obj.sample.all()]))
    project_count.short_description = '项目数'

    def sample_count(self, obj):
        return obj.sample.all().count()
    sample_count.short_description = '样品数'

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_submit:
            return ['slug', 'date', 'sample', 'is_submit']
        return ['slug', 'date']

    def save_model(self, request, obj, form, change):
        # 选中提交复选框时自动记录提交时间
        if obj.is_submit and not obj.date:
            obj.date = date.today()
            projects = []
            for sample in form.instance.__sample__:
                ExtTask.objects.create(sample=sample)
                projects.append(sample.project)
            for i in set(projects):
                if not i.due_date:
                    cycle = i.ext_cycle + i.lib_cycle + i.ana_cycle
                    i.due_date = add_business_days(date.today(), cycle)
                    i.save()
        obj.save()


class QcSubmitForm(forms.ModelForm):
    # 如果需要提取的显示已经合格的样品，已经质检合格的或正在质检的不显示
    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        if 'sample' in self.fields:
            ext_values = set(SampleInfo.is_ext_objects.values_list('pk', flat=True))\
                        - set(ExtTask.objects.filter(result=True).values_list('sample__pk', flat=True))
            qc_values = QcTask.objects.all().values_list('sample__pk', flat=True)
            self.fields['sample'].queryset = SampleInfo.is_qc_objects.exclude(id__in=list(ext_values))\
                .exclude(id__in=list(set(qc_values)))

    def clean(self):
        self.instance.__sample__ = self.cleaned_data['sample']


class QcSubmitAdmin(admin.ModelAdmin):
    form = QcSubmitForm
    list_display = ['slug', 'contract_count', 'project_count', 'sample_count', 'date', 'is_submit']
    filter_horizontal = ('sample',)
    fields = ('slug', 'date', 'sample', 'is_submit')

    def contract_count(self, obj):
        return len(set(i.project.contract.contract_number for i in obj.sample.all()))
    contract_count.short_description = '合同数'

    def project_count(self, obj):
        return len(set([i.project.name for i in obj.sample.all()]))
    project_count.short_description = '项目数'

    def sample_count(self, obj):
        return obj.sample.all().count()
    sample_count.short_description = '样品数'

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_submit:
            return ['slug', 'date', 'sample', 'is_submit']
        return ['slug', 'date']

    def save_model(self, request, obj, form, change):
        # 选中提交复选框时自动记录提交时间
        if obj.is_submit and not obj.date:
            obj.date = date.today()
            projects = []
            for sample in form.instance.__sample__:
                QcTask.objects.create(sample=sample)
                projects.append(sample.project)
            for i in set(projects):
                print(i.due_date)
                if not i.due_date:
                    print(i.qc_cycle)
                    cycle = i.qc_cycle + i.ext_cycle + i.lib_cycle + i.ana_cycle
                    print(cycle)
                    i.due_date = add_business_days(date.today(), cycle)
                    i.save()
        obj.save()


class LibSubmitForm(forms.ModelForm):
    # 如果需要质检的显示已经合格和可以风险建库的样品，已经建库合格的或正在建库的不显示
    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        if 'sample' in self.fields:
            qc_values = set(SampleInfo.is_ext_objects.values_list('pk', flat=True))\
                         - set(QcTask.objects.filter(result__in=[1, 2]).values_list('sample__pk', flat=True))
            lib_values = LibTask.objects.exclude(result=False).values_list('sample__pk', flat=True)
            self.fields['sample'].queryset = SampleInfo.is_lib_objects.exclude(id__in=list(qc_values))\
                .exclude(id__in=list(set(lib_values)))

    def clean(self):
        self.instance.__sample__ = self.cleaned_data['sample']


class LibSubmitAdmin(admin.ModelAdmin):
    form = LibSubmitForm
    list_display = ['slug', 'contract_count', 'project_count', 'sample_count', 'date', 'is_submit']
    filter_horizontal = ('sample',)
    fields = ('slug', 'date', 'sample', 'is_submit')

    def contract_count(self, obj):
        return len(set(i.project.contract.contract_number for i in obj.sample.all()))
    contract_count.short_description = '合同数'

    def project_count(self, obj):
        return len(set([i.project.name for i in obj.sample.all()]))
    project_count.short_description = '项目数'

    def sample_count(self, obj):
        return obj.sample.all().count()
    sample_count.short_description = '样品数'

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_submit:
            return ['slug', 'date', 'sample', 'is_submit']
        return ['slug', 'date']

    def save_model(self, request, obj, form, change):
        # 选中提交复选框时自动记录提交时间
        if obj.is_submit and not obj.date:
            obj.date = date.today()
            projects = []
            for sample in form.instance.__sample__:
                LibTask.objects.create(sample=sample)
                projects.append(sample.project)
            for i in set(projects):
                if not i.due_date:
                    cycle = i.lib_cycle + i.ana_cycle
                    i.due_date = add_business_days(date.today(), cycle)
                    i.save()
        obj.save()


admin.site.register(Project, ProjectAdmin)
admin.site.register(QcSubmit, QcSubmitAdmin)
admin.site.register(ExtSubmit, ExtSubmitAdmin)
admin.site.register(LibSubmit, LibSubmitAdmin)
