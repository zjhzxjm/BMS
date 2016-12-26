from django.contrib import admin
# from .models import Primer, Barcode
from .models import Experiment


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
    list_display = ('sample', 'status')
    readonly_fields = ['sample']

# admin.site.register(Primer, PrimerAdmin)
# admin.site.register(Barcode, BarcodeAdmin)
admin.site.register(Experiment, ExperimentAdmin)