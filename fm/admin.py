from django.contrib import admin
from .models import Bill, Invoice
from datetime import datetime
from django.contrib import messages
from django.contrib.admin.views.main import ChangeList
from django.db.models import Sum
from django.forms.models import BaseInlineFormSet
from daterange_filter.filter import DateRangeFilter
from django.contrib.auth.models import User


class InvoiceChangeList(ChangeList):
    def get_results(self, *args, **kwargs):
        super(InvoiceChangeList, self).get_results(*args, **kwargs)
        self.sum = []
        q_income = self.result_list.aggregate(income_sum=Sum('bill__income'))
        q_amount = self.result_list.aggregate(amount_sum=Sum('invoice__invoice__invoice__amount'))
        try:
            receivable_sum = (q_amount['amount_sum'] or 0) - (q_income['income_sum'] or 0)
            self.sum = [receivable_sum, q_income['income_sum']]
        except KeyError:
            self.sum = ['', '']


class BillInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super(BillInlineFormSet, self).clean()
        total = 0
        for form in self.forms:
            if not form.is_valid():
                return
            if form.cleaned_data and not form.cleaned_data['DELETE']:
                total += form.cleaned_data['income']
        self.instance.__total__ = total


class BillInline(admin.TabularInline):
    model = Bill
    formset = BillInlineFormSet
    extra = 1


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
            return queryset.filter(invoice__contract__salesman__in=list(User.objects.filter(groups__id=3)))
        if self.value() == 'company':
            return queryset.filter(invoice__contract__salesman__in=list(User.objects.filter(groups__in=6)))
        qs = User.objects.filter(groups__in=[3, 6])
        for i in qs:
            if self.value() == i.username:
                return queryset.filter(invoice__contract__salesman=i)


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_contract_number', 'invoice_contract_name', 'contract_amount', 'salesman_name',
                    'contract_type', 'invoice_period', 'invoice_title', 'invoice_amount', 'income_date',
                    'bill_receivable', 'invoice_code', 'date', 'tracking_number', 'send_date')
    list_display_links = ['invoice_title', 'invoice_amount']
    search_fields = ['invoice__title']
    inlines = [
        BillInline,
    ]
    fieldsets = (
        ('申请信息', {
           'fields': ('invoice_title', 'invoice_amount', 'invoice_note')
        }),
        ('开票信息', {
            'fields': ('invoice_code', 'date')  # 历史数据添加时临时调取'date'
        }),
        ('邮寄信息', {
            'fields': ('tracking_number', 'send_date')  # 历史数据添加时临时调取'send_date'
        })
    )

    def invoice_contract_number(self, obj):
        return obj.invoice.contract.contract_number
    invoice_contract_number.short_description = '合同号'

    def invoice_contract_name(self, obj):
        return obj.invoice.contract.name
    invoice_contract_name.short_description = '合同名'

    def contract_amount(self, obj):
        amount = obj.invoice.contract.fis_amount + obj.invoice.contract.fin_amount
        return amount
    contract_amount.short_description = '合同额'

    def salesman_name(self, obj):
        name = obj.invoice.contract.salesman.last_name + obj.invoice.contract.salesman.first_name
        if name:
            return name
        return obj.invoice.contract.salesman
    salesman_name.short_description = '业务员'

    def contract_type(self, obj):
        return obj.invoice.contract.get_type_display()
    contract_type.short_description = '类型'

    def invoice_period(self, obj):
        return obj.invoice.get_period_display()
    invoice_period.short_description = '款期'

    def invoice_title(self, obj):
        return obj.invoice.title
    invoice_title.short_description = '发票抬头'

    def invoice_amount(self, obj):
        return obj.invoice.amount
    invoice_amount.short_description = '发票金额'

    def invoice_note(self, obj):
        return obj.invoice.note
    invoice_note.short_description = '备注'

    # def bill_income(self, obj):
    #     current_income_amounts = Bill.objects.filter(invoice__id=obj.id).values_list('income', flat=True)
    #     return sum(current_income_amounts)
    # bill_income.short_description = '到账金额'

    def bill_receivable(self, obj):
        """
        改进：是否可以接收来自于bill_income的计算值，避免重读查询
        :param obj:
        :return:
        """
        current_income_amounts = Bill.objects.filter(invoice__id=obj.id).values_list('income', flat=True)
        receivable = obj.invoice.invoice.invoice.amount - sum(current_income_amounts)
        return receivable
    bill_receivable.short_description = '应收金额'

    def save_model(self, request, obj, form, change):
        if obj.invoice_code and not obj.date:
            obj.date = datetime.now()
        elif not obj.invoice_code:
            obj.date = None
        if obj.tracking_number and not obj.send_date:
            obj.send_date = datetime.now()
        elif not obj.tracking_number:
            obj.send_date = None
        obj.save()

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        if instances:
            sum_income = formset.instance.__total__
            invoice_amount = instances[0].invoice.invoice.amount
            obj_invoice = Invoice.objects.get(id=instances[-1].invoice_id)
            obj_invoice.income_date = instances[-1].date
            obj_invoice.save()
            if sum_income <= invoice_amount:
                for instance in instances:
                    instance.save()
                formset.save_m2m()
            else:
                messages.set_level(request, messages.ERROR)
                self.message_user(request, '进账总额 %.2f 超过开票金额 %.2f' % (sum_income, invoice_amount),
                                  level=messages.ERROR)

    def get_list_display_links(self, request, list_display):
        # 没有删除发票权限人员，取消入口
        if not request.user.has_perm('fm.delete_invoice'):
            return None
        return ['invoice_title', 'invoice_amount']

    def get_changelist(self, request):
        return InvoiceChangeList

    def get_actions(self, request):
        # 无删除或新增权限人员取消actions
        actions = super(InvoiceAdmin, self).get_actions(request)
        if not request.user.has_perm('fm.delete_invoice') or not request.user.has_perm('fm.add_invoice'):
            actions = None
        return actions

    def get_readonly_fields(self, request, obj=None):
        if not request.user.has_perm('fm.add_invoice'):
            return ['invoice_title', 'invoice_amount', 'invoice_note', 'invoice_code', 'tracking_number']
        return ['invoice_title', 'invoice_amount', 'invoice_note']

    def get_formsets_with_inlines(self, request, obj=None):
        # add page不显示BillInline
        for inline in self.get_inline_instances(request, obj):
            if isinstance(inline, BillInline) and obj is None:
                continue
            if not obj.invoice_code:
                continue
            yield inline.get_formset(request, obj), inline

    def get_queryset(self, request):
        # 只允许管理员和拥有该模型删除权限的人员才能查看所有
        qs = super(InvoiceAdmin, self).get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('fm.delete_invoice'):
            return qs
        return qs.filter(invoice__contract__salesman=request.user)

    def get_list_filter(self, request):
        if request.user.is_superuser or request.user.has_perm('fm.delete_invoice'):
            return [
                SaleListFilter,
                'invoice__contract__type',
                ('income_date', DateRangeFilter),
                ('date', DateRangeFilter)
            ]
        return [
            'invoice__contract__type',
            ('income_date', DateRangeFilter),
            ('date', DateRangeFilter)
        ]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_delete'] = False
        if not Invoice.objects.get(id=object_id).invoice_code and not request.user.has_perm('fm.add_invoice'):
            extra_context['show_save'] = False
            extra_context['show_save_as_new'] = False
            extra_context['show_save_and_continue'] = False
        return super(InvoiceAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)


class BillChangeList(ChangeList):
    def get_results(self, *args, **kwargs):
        super(BillChangeList, self).get_results(*args, **kwargs)
        q = self.result_list.aggregate(Sum('income'))
        self.income_count = q['income__sum']


class BillAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'income', 'date')
    raw_id_fields = ['invoice']
    date_hierarchy = 'date'

    def get_changelist(self, request):
        return BillChangeList

    def save_model(self, request, obj, form, change):
        """
        1、无发票单号不能登记
        2、进账必须大于0
        3、进账总额不能超过开票金额
        """
        invoice_amount = obj.invoice.invoice.invoice.invoice.amount
        current_invoice_amounts = Bill.objects.filter(invoice=obj.invoice).exclude(id=obj.id).values_list('income', flat=True)
        sum_income = obj.income + sum(current_invoice_amounts)
        if not obj.invoice.invoice_code:
            messages.set_level(request, messages.WARNING)
            self.message_user(request, '不能对无单号发票登记进账', level=messages.WARNING)
        elif obj.income <= 0:
            messages.set_level(request, messages.ERROR)
            self.message_user(request, '进账登记必须大于零', level=messages.ERROR)
        elif invoice_amount < sum_income:
            messages.set_level(request, messages.ERROR)
            self.message_user(request, '进账总额 %.2f 超过开票金额 %.2f' % (sum_income, invoice_amount), level=messages.ERROR)
        else:
            obj.save()


admin.site.register(Invoice, InvoiceAdmin)
# admin.site.register(Bill, BillAdmin)
