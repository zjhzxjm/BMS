from django.contrib import admin
from .models import Bill, Invoice
from datetime import datetime
from django.contrib import messages
from django.contrib.admin.views.main import ChangeList
from django.db.models import Sum


class BillInline(admin.TabularInline):
    model = Bill
    extra = 0


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_title', 'invoice_amount', 'bill_income', 'bill_receivable', 'invoice_code', 'date')
    inlines = [
        BillInline,
    ]
    readonly_fields = ('invoice_title', 'invoice_amount')
    fieldsets = (
        ('申请信息', {
           'fields': ('invoice_title', 'invoice_amount')
        }),
        ('开票信息', {
            'fields': ('invoice_code', )
        })
    )

    def invoice_title(self, obj):
        return obj.invoice.title
    invoice_title.short_description = '发票抬头'

    def invoice_amount(self, obj):
        return obj.invoice.amount
    invoice_amount.short_description = '发票金额'

    def bill_income(self, obj):
        current_income_amounts = Bill.objects.filter(invoice__id=obj.id).values_list('income', flat=True)
        return sum(current_income_amounts)
    bill_income.short_description = '到账金额'

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
        obj.save()


class MyChangeList(ChangeList):
    def get_results(self, *args, **kwargs):
        super(MyChangeList, self).get_results(*args, **kwargs)
        q = self.result_list.aggregate(income_sum=Sum('income'))
        self.income_count = q['income_sum']


class BillAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'income', 'date')
    raw_id_fields = ['invoice']
    # list_filter = ['date']
    date_hierarchy = 'date'

    def get_changelist(self, request):
        return MyChangeList

    def save_model(self, request, obj, form, change):
        """
        1、无发票单号不能登记
        2、进账必须大于0
        3、进账总额不能超过开票金额
        :param request:
        :param obj:
        :param form:
        :param change:
        :return:
        """
        invoice_amount = obj.invoice.invoice.invoice.invoice.amount
        current_invoice_amounts = Bill.objects.filter(invoice=obj.invoice).values_list('income', flat=True)
        sum_income = obj.income + sum(current_invoice_amounts)
        print(sum_income)
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
admin.site.register(Bill, BillAdmin)
