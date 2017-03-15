from django.contrib import admin
from .models import Invoice, Contract
from fm.models import Invoice as fm_Invoice
from fm.models import Bill
from django.contrib import messages
from datetime import datetime
from django.utils.html import format_html
from django import forms
from django.forms.models import BaseInlineFormSet
from daterange_filter.filter import DateRangeFilter
from django.contrib.admin.views.main import ChangeList
from django.db.models import Sum
from django.contrib.auth.models import User


class InvoiceForm(forms.ModelForm):
    # 开票金额与合同对应款期额校验 #22
    def clean_amount(self):
        obj_contract = Contract.objects.filter(contract_number=self.cleaned_data['contract']).first()
        if self.cleaned_data['period'] == 'FIS':
            q = Invoice.objects.filter(contract=self.cleaned_data['contract']).filter(period='FIS')\
                .aggregate(Sum('amount'))
            if q['amount__sum'] + self.cleaned_data['amount'] > obj_contract.fis_amount:
                raise forms.ValidationError('首款已开票金额%s元，超出可开票总额' % q['amount__sum'])
        if self.cleaned_data['period'] == 'FIN':
            q = Invoice.objects.filter(contract=self.cleaned_data['contract']).filter(period='FIN')\
                .aggregate(Sum('amount'))
            if q['amount__sum'] + self.cleaned_data['amount'] > obj_contract.fin_amount:
                raise forms.ValidationError('尾款已开票金额%s元，超出可开票总额' % q['amount__sum'])
        return self.cleaned_data['amount']


class InvoiceAdmin(admin.ModelAdmin):
    """
    Admin class for invoice
    """
    form = InvoiceForm
    list_display = ('contract', 'title', 'period', 'amount', 'note', 'submit')
    actions = ['make_invoice_submit']
    list_display_links = None
    fields = ('contract', 'title', 'period', 'amount', 'note')

    def make_invoice_submit(self, request, queryset):
        """
        批量提交开票申请
        """
        i = ''
        n = 0
        for obj in queryset:
            if not obj.submit:
                i = fm_Invoice.objects.create(invoice=obj)
                obj.submit = True
                obj.save()
            else:
                n += 1
        if i:
            self.message_user(request, '%s 个开票申请已成功提交到财务' % i)
        if n:
            self.message_user(request, '%s 个开票申请已提交过，不能再次提交' % n, level=messages.ERROR)
    make_invoice_submit.short_description = '提交开票申请到财务'


class InvoiceInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super(InvoiceInlineFormSet, self).clean()
        total = {}
        total['fis'] = 0
        total['fin'] = 0
        for form in self.forms:
            if not form.is_valid():
                return
            if form.cleaned_data and not form.cleaned_data['DELETE']:
                if form.cleaned_data['period'] == 'FIS':
                    total['fis'] += form.cleaned_data['amount']
                if form.cleaned_data['period'] == 'FIN':
                    total['fin'] += form.cleaned_data['amount']
            self.instance.__total__ = total


class InvoiceInline(admin.StackedInline):
    model = Invoice
    formset = InvoiceInlineFormSet
    extra = 1
    fields = ('title', 'period', 'amount', 'note')


class ContractChangeList(ChangeList):
    def get_results(self, *args, **kwargs):
        super(ContractChangeList, self).get_results(*args, **kwargs)
        fis_amount = self.result_list.aggregate(fis_sum=Sum('fis_amount'))
        fin_amount = self.result_list.aggregate(fin_sum=Sum('fin_amount'))
        self.amount = (fis_amount['fis_sum'] or 0) + (fin_amount['fin_sum'] or 0)


class SaleListFilter(admin.SimpleListFilter):
    title = '业务员'
    parameter_name = 'Sale'

    def lookups(self, request, model_admin):
        qs_sale = User.objects.filter(groups__id=3)
        qs_company = User.objects.filter(groups__id=6)
        value = ['sale'] + list(qs_sale.values_list('username', flat=True)) + \
                ['company'] + list(qs_company.values_list('username', flat=True))
        label = ['销售'] + ['——' + i.last_name + i.first_name for i in qs_sale] + \
                ['公司'] + ['——' + i.last_name + i.first_name for i in qs_company]
        return tuple(zip(value, label))

    def queryset(self, request, queryset):
        if self.value() == 'sale':
            return queryset.filter(salesman__in=list(User.objects.filter(groups__id=3)))
        if self.value() == 'company':
            return queryset.filter(salesman__in=list(User.objects.filter(groups__id=6)))
        qs = User.objects.filter(groups__in=[3, 6])
        for i in qs:
            if self.value() == i.username:
                return queryset.filter(salesman=i)


class ContractAdmin(admin.ModelAdmin):
    """
    Admin class for Contract
    """
    list_display = ('contract_number', 'name', 'type', 'salesman_name', 'price', 'range', 'total', 'fis_income',
                    'fin_income', 'send_date', 'tracking_number', 'receive_date', 'file_link')
    inlines = [
        InvoiceInline,
    ]
    ordering = ['-id']
    fieldsets = (
        ('基本信息', {
            'fields': ('contract_number', 'name', 'type', 'salesman', ('price', 'range'), ('fis_amount', 'fin_amount'))
        }),
        ('邮寄信息', {
            'fields': ('tracking_number', 'send_date', 'receive_date')  # 历史数据添加时临时调取'send_date'和'receive_date'
        }),
        ('上传合同', {
            'fields': ('contract_file',)
        })
    )
    raw_id_fields = ['salesman']
    search_fields = ['contract_number', 'name', 'tracking_number']
    actions = ['make_receive']

    def salesman_name(self, obj):
        # 销售用户名或姓名显示
        name = obj.salesman.last_name + obj.salesman.first_name
        if name:
            return name
        return obj.salesman
    salesman_name.short_description = '业务员'

    def total(self, obj):
        # 总款计算并显示
        amount = obj.fis_amount + obj.fin_amount
        return amount
    total.short_description = '总款'

    def fis_income(self, obj):
        # 首款到账信息显示
        q_income = Bill.objects.filter(invoice__invoice__contract=obj).filter(invoice__invoice__period='FIS')
        income = q_income.aggregate(total_income=Sum('income'))['total_income'] or 0
        if income:
            date = q_income.last().date
            amount = obj.fis_amount
            t = amount - income
            if t > 0:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s / %s' % (income, amount))
            else:
                obj.fis_date = date
                obj.save()
                return '%s/%s' % (income, date)
        return '0/%s' % obj.fis_amount
    fis_income.short_description = '首款'

    def fin_income(self, obj):
        # 尾款到账信息显示
        q_income = Bill.objects.filter(invoice__invoice__contract=obj).filter(invoice__invoice__period='FIN')
        income = q_income.aggregate(total_income=Sum('income'))['total_income'] or 0
        if income:
            date = q_income.last().date
            amount = obj.fin_amount
            t = amount - income
            if t > 0:
                return format_html('<span style="color:{};">{}</span>', 'red', '%s / %s' % (income, amount))
            else:
                obj.fin_date = date
                obj.save()
                return '%s/%s' % (income, date)
        return '0/%s' % obj.fin_amount
    fin_income.short_description = '尾款'

    def make_receive(self, request, queryset):
        # 批量记录合同回寄时间戳
        rows_updated = queryset.update(receive_date=datetime.now())
        if rows_updated:
            self.message_user(request, '%s 个合同寄到登记已完成' % rows_updated)
        else:
            self.message_user(request, '%s 未能成功登记' % rows_updated, level=messages.ERROR)
    make_receive.short_description = '登记所选合同已收到'

    def get_changelist(self, request):
        return ContractChangeList

    def get_list_display_links(self, request, list_display):
        if not request.user.has_perm('mm.add_contract'):
            return
        return ['contract_number']

    def get_actions(self, request):
        actions = super(ContractAdmin, self).get_actions(request)
        if not request.user.has_perm('mm.delete_contract'):
            actions = None
        return actions

    # def get_readonly_fields(self, request, obj=None):
        # if obj.send_date:
        #     return ['contract_number', 'name', 'price', 'range', 'fis_amount', 'fin_amount', 'contract_file']
        # return

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            if isinstance(inline, InvoiceInline) and obj is None:
                continue
            yield inline.get_formset(request, obj), inline

    def get_queryset(self, request):
        # 只允许管理员和该模型新增权限的人员才能查看所有样品
        qs = super(ContractAdmin, self).get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('mm.add_contract'):
            return qs
        return qs.filter(salesman=request.user)

    def get_list_filter(self, request):
        if request.user.is_superuser or request.user.has_perm('mm.add_contract'):
            return [
                SaleListFilter,
                'type',
                ('send_date', DateRangeFilter),
            ]
        return [
            'type',
            ('send_date', DateRangeFilter),
        ]

    def get_readonly_fields(self, request, obj=None):
        if not request.user.has_perm('mm.delete_contract'):
            return ['contract_number', 'name', 'type', 'salesman', 'price', 'range', 'fis_amount', 'fin_amount',
                    'tracking_number', 'send_date', 'receive_date', 'contract_file']
        return []

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        if instances:
            fis_amount = instances[0].contract.fis_amount
            fin_amount = instances[0].contract.fin_amount
            if fis_amount >= formset.instance.__total__['fis'] and fin_amount >= formset.instance.__total__['fin']:
                for instance in instances:
                    instance.save()
                formset.save_m2m()
            else:
                messages.set_level(request, messages.ERROR)
                self.message_user(request, '开票申请总额超过对应款期可开额度,未成功添加开票', level=messages.ERROR)

    def save_model(self, request, obj, form, change):
        """
        1、新增快递单号时自动记录时间戳
        """
        if obj.tracking_number and not obj.send_date:
            obj.send_date = datetime.now()
        elif not obj.tracking_number:
            obj.send_date = None
        obj.save()

admin.site.register(Contract, ContractAdmin)
admin.site.register(Invoice, InvoiceAdmin)
