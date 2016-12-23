from django.contrib import admin
from .models import Customer


class CustomerAdmin(admin.ModelAdmin):
    """
    Admin class for customer
    """
    list_display = ('name', 'organization', 'email', 'phone', 'call', 'address')

admin.site.register(Customer, CustomerAdmin)
