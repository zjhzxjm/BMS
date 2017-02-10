from django.contrib import admin
from .models import Customer, Intention, IntentionRecord
from datetime import date
from django.contrib import messages
from django import forms


class CustomerAdmin(admin.ModelAdmin):
    """
    Admin class for customer
    """
    list_display = ('name', 'organization', 'department', 'address', 'title', 'contact', 'email', 'level')
    ordering = ['name']
    list_filter = ['organization', 'level']
    search_fields = ['name', 'organization', 'contact']
    fieldsets = (
        (None, {
            'fields': ('name', ('organization', 'department'), 'address', 'title', 'contact', 'email', 'level')
        }),
    )

    def get_queryset(self, request):
        # 只允许管理员和拥有该模型删除权限的人员才能查看所有样品
        qs = super(CustomerAdmin, self).get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('crm.delete_customer'):
            return qs
        return qs.filter(linker=request.user)

    def save_model(self, request, obj, form, change):
        obj.linker = request.user
        obj.save()


class IntentionRecordInline(admin.StackedInline):
    model = IntentionRecord
    extra = 1
    exclude = ['record_date']

    def get_readonly_fields(self, request, obj=None):
        # 没有新增意向权限人员仅能查看信息
        if not request.user.has_perm('crm.add_intention'):
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields


class IntentionForm(forms.ModelForm):
    def clean_price(self):
        if int(self.cleaned_data.get('price')) < 0:
            raise forms.ValidationError('预计成交价不能小于0')
        return self.cleaned_data['price']

    def clean_closing_date(self):
        if self.cleaned_data.get('closing_date') < date.today():
            raise forms.ValidationError('预计成交时间不能早于今日')
        return self.cleaned_data['closing_date']


class IntentionAdmin(admin.ModelAdmin):
    """
    Admin class for intention
    """
    form = IntentionForm
    list_display = ('customer_organization', 'customer_name', 'project_name', 'project_type', 'amount', 'closing_date',
                    'price', 'status')
    list_filter = ['project_type', 'closing_date', 'amount']
    inlines = [
        IntentionRecordInline,
    ]
    fields = ('customer_organization', 'customer', 'project_name', 'project_type', 'amount', 'closing_date', 'price')
    raw_id_fields = ('customer',)

    def get_list_display_links(self, request, list_display):
        # 没有新增意向权限人员，入口设置为状态，否则为项目名
        if not request.user.has_perm('crm.add_intention'):
            return ['status']
        return ['project_name']

    def customer_organization(self, obj):
        return obj.customer.organization
    customer_organization.short_description = '单位'

    def customer_name(self, obj):
        return obj.customer.name
    customer_name.short_description = '客户姓名'

    def status(self, obj):
        return IntentionRecord.objects.filter(intention_id=obj.id).last().status
    status.short_description = '最新进展'

    def get_queryset(self, request):
        # 只允许管理员和拥有该模型删除权限的人员才能查看所有样品
        qs = super(IntentionAdmin, self).get_queryset(request)
        if request.user.is_superuser or request.user.has_perm('crm.delete_intention'):
            return qs
        return qs.filter(customer__linker=request.user)

    def get_actions(self, request):
        # 无删除权限人员取消actions
        actions = super(IntentionAdmin, self).get_actions(request)
        if not request.user.has_perm('crm.delete_intention'):
            actions = None
        return actions

    def get_readonly_fields(self, request, obj=None):
        # 没有新增意向权限人员仅能查看信息
        if not request.user.has_perm('crm.add_intention'):
            return ['customer_organization', 'customer', 'project_name', 'project_type', 'amount', 'closing_date',
                    'price']
        return ['customer_organization']

    def change_view(self, request, object_id, form_url='', extra_context=None):
        # 没有新增意向权限人员查看页面时隐藏所有按钮
        extra_context = extra_context or {}
        if not request.user.has_perm('crm.add_intention'):
            extra_context['show_save'] = False
            extra_context['show_save_as_new'] = False
            # extra_context['show_save_and_add_another'] = False
            extra_context['show_save_and_continue'] = False
        return super(IntentionAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def save_formset(self, request, form, formset, change):
        # 历史记录禁止修改
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        if instances:
            for instance in instances:
                if instance.record_date < date.today():
                    self.message_user(request, '%s 历史进展记录未被允许修改' % instance.record_date, level=messages.WARNING)
                    continue
                instance.save()
            formset.save_m2m()

admin.site.register(Intention, IntentionAdmin)
admin.site.register(Customer, CustomerAdmin)
