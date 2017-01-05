from django.contrib import admin
from .models import Bill, Invoice


class BillInline(admin.TabularInline):
    model = Bill
    extra = 0


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_title', 'invoice_amount', 'invoice_code', 'date')
    inlines = [
        BillInline,
    ]

    def invoice_title(self, obj):
        return obj.invoice.title
    invoice_title.short_description = '发票抬头'

    def invoice_amount(self, obj):
        return obj.invoice.amount
    invoice_amount.short_description = '发票金额'

admin.site.register(Invoice, InvoiceAdmin)



