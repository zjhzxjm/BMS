from django.contrib import admin
from .models import Customer


class CustomerAdmin(admin.ModelAdmin):
    """
    Admin class for customer
    """
    list_display = ('name', 'organization', 'email', 'phone', 'call', 'address')
    ordering = ['name']
    list_filter = ['organization']
    search_fields = ['name', 'organization', 'phone', 'call']

    def get_queryset(self, request):
        # 只允许管理员和拥有该模型删除权限的人员才能查看所有样品
        qs = super(CustomerAdmin, self).get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('crm.delete_custom'):
            return qs
        return qs.filter(linker=request.user)

admin.site.register(Customer, CustomerAdmin)
