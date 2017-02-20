from django.contrib import admin
from .models import Invoice, Contract
from fm.models import Invoice as fm_Invoice
from fm.models import Bill
from django.contrib import messages
from datetime import datetime
from django.db.models import Sum
from django.utils.html import format_html


class InvoiceAdmin(admin.ModelAdmin):
    """
    Admin class for invoice
    """
    list_display = ('contract', 'title', 'period', 'amount', 'note', 'submit')
    actions = ['make_invoice_submit']
    list_display_links = None
    fields = ('contract', 'title', 'period', 'amount', 'note')

    def make_invoice_submit(self, request, queryset):
        """
        批量提交开票申请
        :param request:
        :param queryset:
        :return:
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


class InvoiceInline(admin.StackedInline):
    model = Invoice
    extra = 1
    fields = ('title', 'period', 'amount', 'note')


class ContractAdmin(admin.ModelAdmin):
    """
    Admin class for Contract
    """
    list_display = ('contract_number', 'name', 'salesman_name', 'price', 'range', 'total', 'fis_income', 'fin_income',
                    'send_date', 'tracking_number', 'receive_date', 'file_link')
    list_filter = (
        ('salesman', admin.RelatedOnlyFieldListFilter),
    )
    inlines = [
        InvoiceInline,
    ]
    ordering = ['-id']
    fieldsets = (
        ('基本信息', {
            'fields': ('contract_number', 'name', 'salesman', ('price', 'range'), ('fis_amount', 'fin_amount'))
        }),
        ('邮寄信息', {
            'fields': ('tracking_number',)
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
    salesman_name.short_description = '销售'

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
        """
        批量记录合同回寄时间戳
        :param request:
        :param queryset:
        :return:
        """
        rows_updated = queryset.update(receive_date=datetime.now())
        if rows_updated:
            self.message_user(request, '%s 个合同寄到登记已完成' % rows_updated)
        else:
            self.message_user(request, '%s 未能成功登记' % rows_updated, level=messages.ERROR)
    make_receive.short_description = '登记所选合同已收到'

    def get_readonly_fields(self, request, obj=None):
        if obj.send_date:
            return ['contract_number', 'name', 'price', 'range', 'fis_amount', 'fin_amount']
        return ['']

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

    def save_model(self, request, obj, form, change):
        """
        新增快递单号时自动记录时间戳
        :param request:
        :param obj:
        :param form:
        :param change:
        :return:
        """
        if obj.tracking_number and not obj.send_date:
            obj.send_date = datetime.now()
        obj.save()

admin.site.register(Contract, ContractAdmin)
admin.site.register(Invoice, InvoiceAdmin)
