from django.contrib import admin
from .models import Project, Sample, SequenceInfo, Library
from django.utils.html import format_html


class SampleInline(admin.TabularInline):
    model = Sample


class ProjectAdmin(admin.ModelAdmin):
    """
    Admin class for project
    """
    list_display = ('contract_number', 'name', 'customer', 'customer_organization', 'init_date', 'color_status')
    inlines = [
        SampleInline,
    ]

    def customer_organization(self, obj):
        return obj.customer.organization
    customer_organization.short_description = '单位'

    def color_status(self, obj):
        t = obj.status
        colors = ['red', 'yellow', 'blue', 'orange', 'pink', 'green']
        style = '<span style="color:{};">{}</span>'
        if t == 'NST':
            return format_html(style, colors[0], '未启动',)
        elif t == 'SSB':
            return format_html(style, colors[1], '样品提交',)
        elif t == 'QC':
            return format_html(style, colors[2], '质控完成',)
        elif t == 'LIB':
            return format_html(style, colors[3], '建库完成',)
        elif t == 'SEQ':
            return format_html(style, colors[4], '测序完成',)
        elif t == 'FIN':
            return format_html(style, colors[5], '完结',)
    color_status.short_description = '状态'


class SequenceInfoInline(admin.TabularInline):
    model = SequenceInfo
    raw_id_fields = ('sample',)


class LibraryAdmin(admin.ModelAdmin):
    """
    Admin class for library
    """
    list_display = ('name',)
    inlines = [
        SequenceInfoInline,
    ]


    # def sample_project(self, obj):
    #     return obj.sample.project
    # sample_project.short_description = '项目'
    #
    # def sample_contract_data(self, obj):
    #     return obj.sample.contract_data
    # sample_contract_data.short_description = '合同数据量'


admin.site.register(Project, ProjectAdmin)
admin.site.register(Library, LibraryAdmin)


