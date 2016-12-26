from django.contrib import admin
from .models import Project, Sample, SequenceInfo, Library
from lims.models import Experiment
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class SampleResource(resources.ModelResource):
    class Meta:
        model = Sample
        fields = ('id', 'project', 'name', 'contract_data',)


class SampleAdmin(ImportExportModelAdmin):
    """
    Admin class for sample
    """
    resource_class = SampleResource
    list_display = ('project_contract_number', 'project', 'name', 'contract_data')
    ordering = ['project']
    list_filter = ['project']
    actions = ['make_sample_submit']

    def project_contract_number(self, obj):
        return obj.project.contract_number
    project_contract_number.short_description = '合同号'

    def make_sample_submit(self, request ,queryset):
        """
        批量下达任务提交任务
        :param request:
        :param queryset:
        :return:
        """
        i = 0
        for obj in queryset:
            p = Project.objects.update(status='SSB')
            e = Experiment.objects.create(sample=obj)
            i += 1
        if e and p:
            self.message_user(request, '%s 个样品已成功提交到实验室' % i)
        else:
            self.message_user(request, '未能成功提交 %s %s' % (e, rows_updated))
    make_sample_submit.short_description = '提交样品到实验室'


class SampleInline(admin.TabularInline):
    model = Sample
    extra = 0


class ProjectAdmin(admin.ModelAdmin):
    """
    Admin class for project
    """
    list_display = ('id', 'contract_number', 'name', 'count_sample', 'customer', 'customer_organization', 'init_date', 'color_status')
    list_display_links = ['contract_number']
    inlines = [
        SampleInline,
    ]
    ordering = ['-id']
    search_fields = ['contract_number', 'customer__name']
    list_filter = ['status', 'customer__organization', 'customer']

    def customer_organization(self, obj):
        return obj.customer.organization
    customer_organization.short_description = '单位'

    # 状态节点样式化
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

    # 统计样品个数
    def count_sample(self, obj):
        return Sample.objects.sample_count(obj)
    count_sample.short_description = '样品数'

    # 批量设置状态
    def make_nst(self):
        pass


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

admin.site.register(Sample, SampleAdmin)
admin.site.register(Project, ProjectAdmin)
# admin.site.register(Library, LibraryAdmin)


