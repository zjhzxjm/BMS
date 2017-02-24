from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    contract = models.ForeignKey(
        'mm.Contract',
        verbose_name='合同号',
        on_delete=models.CASCADE,
    )
    customer = models.CharField('客户', max_length=20)
    name = models.CharField('项目注解', max_length=100, blank=True)
    service_type = models.CharField('服务类型', max_length=50)
    data_amount = models.CharField('数据要求', max_length=10)
    is_ext = models.BooleanField('需提取')
    is_qc = models.BooleanField('需质检')
    is_lib = models.BooleanField('需建库')
    ext_cycle = models.PositiveIntegerField('提取周期')
    ext_task_cycle = models.PositiveIntegerField('提取周期')
    ext_date = models.DateField('提取完成日', blank=True, null=True)
    qc_cycle = models.PositiveIntegerField('质检周期')
    qc_task_cycle = models.PositiveIntegerField('质检周期')
    qc_date = models.DateField('质检完成日', blank=True, null=True)
    lib_cycle = models.PositiveIntegerField('建库周期')
    lib_task_cycle = models.PositiveIntegerField('建库周期')
    lib_date = models.DateField('建库完成日', blank=True, null=True)
    seq_cycle = models.PositiveIntegerField('测序周期')
    seq_start_date = models.DateField('测序开始日', blank=True, null=True)
    seq_end_date = models.DateField('测序完成日', blank=True, null=True)
    ana_cycle = models.PositiveIntegerField('分析周期')
    ana_start_date = models.DateField('分析开始日', blank=True, null=True)
    ana_end_date = models.DateField('分析完成日', blank=True, null=True)
    report_date = models.DateField('释放报告日', blank=True, null=True)
    result_date = models.DateField('释放结果日', blank=True, null=True)
    data_date = models.DateField('释放数据日', blank=True, null=True)
    due_date = models.DateField('合同节点', blank=True, null=True)
    is_confirm = models.BooleanField('确认', default=False)

    class Meta:
        unique_together = ('contract', 'name')
        verbose_name = '0项目管理'
        verbose_name_plural = '0项目管理'

    def __str__(self):
        return '%s' % self.name


class ExtSubmit(models.Model):
    slug = models.SlugField('任务号', allow_unicode=True)
    sample = models.ManyToManyField(
        'lims.SampleInfo',
        verbose_name='样品',
    )
    date = models.DateField('提交时间', blank=True, null=True)
    is_submit = models.BooleanField('提交')

    def save(self, *args, **kwargs):
        super(ExtSubmit, self).save(*args, **kwargs)
        if not self.slug:
            self.slug = "提取任务 #" + str(self.id)
            self.save()

    class Meta:
        verbose_name = '1提取任务下单'
        verbose_name_plural = '1提取任务下单'

    def __str__(self):
        return '%s' % self.slug


class QcSubmit(models.Model):
    slug = models.SlugField('任务号', allow_unicode=True)
    sample = models.ManyToManyField(
        'lims.SampleInfo',
        verbose_name='样品',
    )
    date = models.DateField('提交时间', blank=True, null=True)
    is_submit = models.BooleanField('提交')

    def save(self, *args, **kwargs):
        super(QcSubmit, self).save(*args, **kwargs)
        if not self.slug:
            self.slug = "质检任务 #" + str(self.id)
            self.save()

    class Meta:
        verbose_name = '2质检任务下单'
        verbose_name_plural = '2质检任务下单'

    def __str__(self):
        return '%s' % self.slug


class LibSubmit(models.Model):
    slug = models.SlugField('任务号', allow_unicode=True)
    sample = models.ManyToManyField(
        'lims.SampleInfo',
        verbose_name='样品'
    )
    date = models.DateField('提交时间', blank=True, null=True)
    is_submit = models.BooleanField('提交')

    def save(self, *args, **kwargs):
        super(LibSubmit, self).save(*args, **kwargs)
        if not self.slug:
            self.slug = "建库任务 #" + str(self.id)
            self.save()

    class Meta:
        verbose_name = '3建库任务下单'
        verbose_name_plural = '3建库任务下单'

    def __str__(self):
        return '%s' % self.slug


