from django.contrib import admin
from .models import Project, QcSubmit, ExtSubmit, LibSubmit
from lims.models import SampleInfo, QcTask, ExtTask, LibTask
from django import forms
from datetime import date, timedelta
from fm.models import Bill
from mm.models import Contract
from django.db.models import Sum
from django.utils.html import format_html
from django.contrib import messages


def add_business_days(from_date, number_of_days):
    to_date = from_date
    if number_of_days >= 0:
        while number_of_days:
            to_date += timedelta(1)
            if to_date.weekday() < 5:
                number_of_days -= 1
    else:
        while number_of_days:
            to_date -= timedelta(1)
            if to_date.weekday() < 5:
                number_of_days += 1
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
            ('ENS', '待处理'),
            ('EXT', '提取中'),
            ('QC', '质检中'),
            ('LIB', '建库中'),
            ('SEQ', '测序中'),
            ('ANA', '分析中'),
            ('FIN', '待尾款'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'FIS':
            return queryset.filter(contract__fis_date=None)
        if self.value() == 'ENS':
            projects = []
            ext_samples = list(set(ExtTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
            projects += list(set(SampleInfo.objects.filter(id__in=ext_samples).values_list('project__pk', flat=True)))

            qc_samples = list(set(QcTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
            projects += list(set(SampleInfo.objects.filter(id__in=qc_samples).values_list('project__pk', flat=True)))

            lib_samples = list(set(LibTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
            projects += list(set(SampleInfo.objects.filter(id__in=lib_samples).values_list('project__pk', flat=True)))

            projects += Project.objects.exclude(seq_start_date=None).filter(seq_end_date=None)\
                .values_list('pk', flat=True)
            projects += Project.objects.exclude(ana_start_date=None).filter(ana_end_date=None)\
                .values_list('pk', flat=True)

            projects += Project.objects.exclude(ana_start_date=None).exclude(ana_end_date=None)\
                .filter(contract__fin_date=None).values_list('pk', flat=True)
            print(projects)
            return queryset.exclude(contract__fis_date=None).exclude(id__in=projects)
        if self.value() == 'EXT':
            samples = list(set(ExtTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
            projects = list(set(SampleInfo.objects.filter(id__in=samples).values_list('project__pk', flat=True)))
            return queryset.filter(id__in=projects)
        if self.value() == 'QC':
            samples = list(set(QcTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
            projects = list(set(SampleInfo.objects.filter(id__in=samples).values_list('project__pk', flat=True)))
            return queryset.filter(id__in=projects)
        if self.value() == 'LIB':
            samples = list(set(LibTask.objects.filter(result=None).values_list('sample__pk', flat=True)))
            projects = list(set(SampleInfo.objects.filter(id__in=samples).values_list('project__pk', flat=True)))
            return queryset.filter(id__in=projects)
        if self.value() == 'SEQ':
            return queryset.exclude(seq_start_date=None).filter(seq_end_date=None)
        if self.value() == 'ANA':
            return queryset.exclude(ana_start_date=None).filter(ana_end_date=None)
        if self.value() == 'FIN':
            return queryset.exclude(ana_start_date=None).exclude(ana_end_date=None).filter(contract__fin_date=None)


class ProjectForm(forms.ModelForm):
    def clean_seq_start_date(self):
        if not self.cleaned_data['seq_start_date']:
            return
        project = Project.objects.filter(contract=self.cleaned_data['contract']).filter(name=self.cleaned_data['name'])\
            .first()
        if project.is_confirm == 0:
            raise forms.ValidationError('项目尚未启动，请留空')
        if not project.is_lib:
            return self.cleaned_data['seq_start_date']
        lib_date = project.lib_date
        if not lib_date:
            raise forms.ValidationError('尚未完成建库，无法记录测序时间')
        elif lib_date > self.cleaned_data['seq_start_date']:
            raise forms.ValidationError('测序开始日期不能早于建库完成日期')
        return self.cleaned_data['seq_start_date']

    def clean_ana_start_date(self):
        if not self.cleaned_data['ana_start_date']:
            return
        if 'seq_end_date' not in self.cleaned_data.keys() or not self.cleaned_data['seq_end_date']:
            raise forms.ValidationError('尚未完成测序，无法记录分析时间')
        elif self.cleaned_data['seq_end_date'] > self.cleaned_data['ana_start_date']:
            raise forms.ValidationError('分析开始日期不能早于测序完成日期')
        return self.cleaned_data['ana_start_date']

    def clean_seq_end_date(self):
        if not self.cleaned_data['seq_end_date']:
            return
        if 'seq_start_date' not in self.cleaned_data.keys() or not self.cleaned_data['seq_start_date']:
            raise forms.ValidationError('尚未记录测序开始日期')
        elif self.cleaned_data['seq_end_date'] and self.cleaned_data['seq_start_date'] \
                > self.cleaned_data['seq_end_date']:
            raise forms.ValidationError('完成日期不能早于开始日期')
        return self.cleaned_data['seq_end_date']

    def clean_ana_end_date(self):
        if not self.cleaned_data['ana_end_date']:
            return
        if 'ana_start_date' not in self.cleaned_data.keys() or not self.cleaned_data['ana_start_date']:
            raise forms.ValidationError('尚未记录分析开始日期')
        elif self.cleaned_data['ana_start_date'] > self.cleaned_data['ana_end_date']:
            raise forms.ValidationError('完成日期不能早于开始日期')
        return self.cleaned_data['ana_end_date']

    def clean_report_date(self):
        if not self.cleaned_data['report_date']:
            return
        if 'ana_end_date' not in self.cleaned_data.keys() or not self.cleaned_data['ana_end_date']:
            raise forms.ValidationError('分析尚未完成')
        return self.cleaned_data['report_date']

    def clean_result_date(self):
        if not self.cleaned_data['result_date']:
            return
        if 'ana_end_date' not in self.cleaned_data.keys() or not self.cleaned_data['ana_end_date']:
            raise forms.ValidationError('分析尚未完成')
        return self.cleaned_data['result_date']

    def clean_data_date(self):
        if not self.cleaned_data['data_date']:
            return
        if not Contract.objects.filter(contract_number=self.cleaned_data['contract']).first().fin_date:
            raise forms.ValidationError('尾款未到不能操作该记录')


# class ProjectAdminFormSet(BaseModelFormSet):
#     def clean(self):
#         for p in self.cleaned_data:
#             if not SampleInfo.objects.filter(project=p['id']).count() and p['is_confirm']:
#                 raise forms.ValidationError('未收到样品的项目无法确认启动')


class ProjectAdmin(admin.ModelAdmin):
    form = ProjectForm
    list_display = ('id', 'contract_name', 'is_confirm', 'status', 'sample_num', 'receive_date',
                    'contract_node', 'ext_status', 'qc_status', 'lib_status', 'seq_status', 'ana_status',
                    'report_sub', 'result_sub', 'data_sub')
    # list_editable = ['is_confirm']
    list_filter = [StatusListFilter]
    fieldsets = (
        ('合同信息', {
           'fields': (('contract', 'contract_name'),)
        }),
        ('项目信息', {
            'fields': ('customer', 'name', ('service_type', 'is_ext', 'is_qc', 'is_lib'), 'data_amount')
        }),
        ('节点信息', {
            'fields': (('seq_start_date', 'seq_end_date'), ('ana_start_date', 'ana_end_date'),
                       ('report_date', 'result_date', 'data_date'))
        }),
        ('项目周期设置(工作日)', {
           'fields': (('ext_cycle', 'qc_cycle', 'lib_cycle', 'seq_cycle', 'ana_cycle'),)
        }),
        ('实验周期设置(工作日)', {
           'fields': (('ext_task_cycle', 'qc_task_cycle', 'lib_task_cycle'),)
        }),
    )
    readonly_fields = ['contract_name']
    raw_id_fields = ['contract']
    actions = ['make_confirm']

    def contract_name(self, obj):
        return obj.contract.name
    contract_name.short_description = '项目名称'

    def status(self, obj):
        if is_period_income(obj.contract, 'FIS') > 0:
            return '待首款'
        if obj.ana_end_date and is_period_income(obj.contract, 'FIN') > 0:
            return '待尾款'
        if obj.ana_start_date and not obj.ana_end_date:
            return '分析中'
        if obj.seq_start_date and not obj.seq_end_date:
            return '测序中'
        if LibTask.objects.filter(sample__project=obj).filter(result=None).count():
            return '建库中'
        if QcTask.objects.filter(sample__project=obj).filter(result=None).count():
            return '质检中'
        if ExtTask.objects.filter(sample__project=obj).filter(result=None).count():
            return '提取中'
        if is_period_income(obj.contract, 'FIS') == 0:
            return '待处理'
    status.short_description = '状态'

    def sample_num(self, obj):
        return SampleInfo.objects.filter(project=obj).count()
    sample_num.short_description = '收样数'

    def receive_date(self, obj):
        qs_sample = SampleInfo.objects.filter(project=obj)
        if qs_sample:
            return qs_sample.last().receive_date.strftime('%Y%m%d')
    receive_date.short_description = '收样时间'

    def contract_node(self, obj):
        if obj.due_date:
            return obj.due_date.strftime('%Y%m%d')
        else:
            return
    contract_node.short_description = '合同节点'

    def report_sub(self, obj):
        if obj.report_date:
            return obj.report_date.strftime('%Y%m%d')
        else:
            return
    report_sub.short_description = '报告提交'

    def result_sub(self, obj):
        if obj.result_date:
            return obj.result_date.strftime('%Y%m%d')
        else:
            return
    result_sub.short_description = '结果提交'

    def data_sub(self, obj):
        if obj.data_date:
            return obj.data_date.strftime('%Y%m%d')
    data_sub.short_description = '数据提交'

    def ext_status(self, obj):
        if not obj.due_date or not obj.is_ext:
            return '-'
        total = ExtTask.objects.filter(sample__project=obj).count()
        done = ExtTask.objects.filter(sample__project=obj).exclude(result=None).count()
        if done != total or not total:
            obj.ext_date = None
            obj.save()
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle + obj.lib_cycle + obj.qc_cycle) -
                    date.today()).days
            if left >= 0:
                return '%s/%s-余%s天' % (done, total, left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s/%s-延%s天' % (done, total, -left))
        else:
            obj.ext_date = ExtTask.objects.filter(sample__project=obj).order_by('-date').first().date
            obj.save()
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle + obj.lib_cycle + obj.qc_cycle) -
                    obj.ext_date).days
            if left >= 0:
                return '%s-提前%s天' % (obj.ext_date.strftime('%Y%m%d'), left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天' %
                                   (obj.ext_date.strftime('%Y%m%d'), -left))
    ext_status.short_description = '提取进度'

    def qc_status(self, obj):
        if not obj.due_date or not obj.is_qc:
            return '-'
        total = QcTask.objects.filter(sample__project=obj).count()
        done = QcTask.objects.filter(sample__project=obj).exclude(result=None).count()
        if done != total or not total:
            obj.qc_date = None
            obj.save()
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle + obj.lib_cycle) - date.today()).days
            if left >= 0:
                return '%s/%s-余%s天' % (done, total, left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s/%s-延%s天' % (done, total, -left))
        else:
            obj.qc_date = QcTask.objects.filter(sample__project=obj).order_by('-date').first().date
            obj.save()
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle + obj.lib_cycle) - obj.qc_date).days
            if left >= 0:
                return '%s-提前%s天' % (obj.qc_date.strftime('%Y%m%d'), left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天' % (obj.qc_date.strftime('%Y%m%d'), -left))
    qc_status.short_description = '质检进度'

    def lib_status(self, obj):
        if not obj.due_date or not obj.is_lib:
            return '-'
        total = LibTask.objects.filter(sample__project=obj).count()
        done = LibTask.objects.filter(sample__project=obj).exclude(result=None).count()
        if done != total or not total:
            obj.lib_date = None
            obj.save()
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle) - date.today()).days
            if left >= 0:
                return '%s/%s-余%s天' % (done, total, left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s/%s-延%s天' % (done, total, -left))
        else:
            obj.lib_date = LibTask.objects.filter(sample__project=obj).order_by('-date').first().date
            obj.save()
            left = (obj.due_date - timedelta(obj.ana_cycle + obj.seq_cycle) - obj.lib_date).days
            if left >= 0:
                return '%s-提前%s天' % (obj.lib_date.strftime('%Y%m%d'), left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天' % (obj.lib_date.strftime('%Y%m%d'), -left))
    lib_status.short_description = '建库进度'

    def seq_status(self, obj):
        if not obj.due_date:
            return '-'
        if not obj.seq_end_date:
            left = (obj.due_date - timedelta(obj.ana_cycle) - date.today()).days
            if left >= 0:
                return '余%s天' % left
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '延%s天' % -left)
        else:
            left = (obj.due_date - timedelta(obj.ana_cycle) - obj.seq_end_date).days
            if left >= 0:
                return '%s-提前%s天' % (obj.seq_end_date.strftime('%Y%m%d'), left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天'
                                   % (obj.seq_end_date.strftime('%Y%m%d'), -left))
    seq_status.short_description = '测序进度'

    def ana_status(self, obj):
        if not obj.due_date:
            return '-'
        if not obj.ana_end_date:
            left = (obj.due_date - date.today()).days
            if left >= 0:
                return '余%s天' % left
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '延%s天' % -left)
        else:
            left = (obj.due_date - obj.ana_end_date).days
            if left >= 0:
                return '%s-提前%s天' % (obj.ana_end_date.strftime('%Y%m%d'), left)
            else:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s-延%s天'
                                   % (obj.ana_end_date.strftime('%Y%m%d'), -left))
    ana_status.short_description = '分析进度'

    def make_confirm(self, request, queryset):
        projects = []
        for obj in queryset:
            qs = SampleInfo.objects.filter(project=obj)
            if not obj.is_ext and not obj.is_qc and not obj.is_lib:
                receive_date = qs.last().receive_date
                cycle = obj.ext_cycle + obj.qc_cycle + obj.lib_cycle + obj.seq_cycle + obj.ana_cycle
                due_date = add_business_days(receive_date, cycle)
                obj.due_date = due_date
                obj.save()
            if qs.count():
                projects += list(set(qs.values_list('project__pk', flat=True)))
        rows_updated = queryset.filter(id__in=projects).update(is_confirm=True)
        select_num = queryset.count()
        if rows_updated:
            self.message_user(request, '%s 个项目已经完成确认可启动, %s 个项目不含样品无法启动'
                              % (rows_updated, select_num-rows_updated))
        else:
            self.message_user(request, '所选项目不含样品或系统问题无法确认启动', level=messages.ERROR)
    make_confirm.short_description = '设置所选项目为确认可启动状态'

    def save_model(self, request, obj, form, change):
        if obj.due_date:
            project = Project.objects.filter(name=obj).first()
            old_cycle = project.ext_cycle + project.qc_cycle + project.lib_cycle + project.seq_cycle + project.ana_cycle
            new_cycle = obj.ext_cycle + obj.qc_cycle + obj.lib_cycle + obj.seq_cycle + obj.ana_cycle
            obj.due_date = add_business_days(project.due_date, new_cycle - old_cycle)
        obj.save()

    # def get_changelist_formset(self, request, **kwargs):
    #     kwargs['formset'] = ProjectAdminFormSet
    #     print(ProjectAdminFormSet)
    #     print(super(ProjectAdmin, self).get_changelist_formset(request, **kwargs))
    #     # if request.user.has_perm('pm.add_project')
    #     return super(ProjectAdmin, self).get_changelist_formset(request, **kwargs)

    def get_list_display_links(self, request, list_display):
        if not request.user.has_perm('pm.add_project'):
            return
        return ['contract_name']

    def get_queryset(self, request):
        # 只允许管理员和拥有该模型新增权限的人员才能查看所有样品
        qs = super(ProjectAdmin, self).get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('pm.add_project'):
            return qs
        return qs.filter(contract__salesman=request.user)

    def get_actions(self, request):
        # 无权限人员取消actions
        actions = super(ProjectAdmin, self).get_actions(request)
        if not request.user.has_perm('pm.add_project'):
            actions = None
        return actions


class ExtSubmitForm(forms.ModelForm):
    # 已经提交提取的样品不显示
    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        if 'sample' in self.fields:
            values = ExtTask.objects.all().values_list('sample__pk', flat=True)
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
                ExtTask.objects.create(sample=sample, sub_date=date.today())
                projects.append(sample.project)
            for i in set(projects):
                if not i.due_date:
                    cycle = i.ext_cycle + i.qc_cycle + i.lib_cycle + i.seq_cycle + i.ana_cycle
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
                QcTask.objects.create(sample=sample, sub_date=date.today())
                projects.append(sample.project)
            for i in set(projects):
                if not i.due_date:
                    cycle = i.qc_cycle + i.lib_cycle + i.seq_cycle + i.ana_cycle
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
                LibTask.objects.create(sample=sample, sub_date=date.today())
                projects.append(sample.project)
            for i in set(projects):
                if not i.due_date:
                    cycle = i.lib_cycle + i.seq_cycle + i.ana_cycle
                    i.due_date = add_business_days(date.today(), cycle)
                    i.save()
        obj.save()


admin.site.register(Project, ProjectAdmin)
admin.site.register(QcSubmit, QcSubmitAdmin)
admin.site.register(ExtSubmit, ExtSubmitAdmin)
admin.site.register(LibSubmit, LibSubmitAdmin)
