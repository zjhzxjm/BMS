from django.contrib import admin
from .models import Invoice, Contract
from fm.models import Invoice as fm_Invoice
from django.contrib import messages
from datetime import datetime


class InvoiceAdmin(admin.ModelAdmin):
    """
    Admin class for invoice
    """
    list_display = ('contract', 'title', 'period', 'amount', 'submit')
    actions = ['make_invoice_submit']
    list_display_links = None
    fields = ('contract', 'title', 'period', 'amount')

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


class InvoiceInline(admin.TabularInline):
    model = Invoice
    extra = 0
    fields = ('title', 'period', 'amount')


class ContractAdmin(admin.ModelAdmin):
    """
    Admin class for Contract
    """
    list_display = ('contract_number', 'name', 'salesman_name', 'price', 'total', 'send_date', 'tracking_number', 'receive_date')
    inlines = [
        InvoiceInline,
    ]
    ordering = ['-id']
    fieldsets = (
        ('基本信息', {
            'fields': ('contract_number', 'name', 'salesman', 'price', 'total')
        }),
        ('邮寄信息', {
            'fields': ('tracking_number',)
        })
    )
    raw_id_fields = ['salesman']
    actions = ['make_receive']

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            if isinstance(inline, InvoiceInline) and obj is None:
                continue
            yield inline.get_formset(request, obj), inline

    def salesman_name(self, obj):
        """
        销售用户名或姓名显示
        :param obj:
        :return:
        """
        name = obj.salesman.last_name + obj.salesman.first_name
        if name:
            return name
        return obj.salesman

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
    salesman_name.short_description = '销售'

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


admin.site.register(Contract, ContractAdmin)
admin.site.register(Invoice, InvoiceAdmin)
