from django.contrib import admin
from .models import Primer, Barcode


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

admin.site.register(Primer, PrimerAdmin)
admin.site.register(Barcode, BarcodeAdmin)