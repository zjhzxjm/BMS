from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    """
    Project class
    """
    STATUS_CHOICES = (
        ('NST', '未启动'),
        ('SSB', '样品提交'),
        ('QC', '质控完成'),
        ('LIB', '建库完成'),
        ('SEQ', '测序完成'),
        ('FIN', '完成'),
        ('PAU', '暂停'),
    )
    contract_number = models.CharField('合同号', max_length=15, unique=True)
    name = models.CharField('项目名', max_length=20, help_text='最大只允许20个字符')
    customer = models.ForeignKey(
        'crm.Customer',
        verbose_name='客户',
    )
    init_date = models.DateTimeField('创建时间', auto_now_add=True)
    status = models.CharField('状态', max_length=3, choices=STATUS_CHOICES, default='NST')
    description = models.TextField('项目简介', blank=True)

    class Meta:
        verbose_name = '项目管理'
        verbose_name_plural = '项目管理'

    def __str__(self):
        return '%s' % self.name


class Library(models.Model):
    """
    Library class
    """
    name = models.CharField('文库名', max_length=15, help_text='最大只允许15个字符')

    class Meta:
        verbose_name = '排机管理'
        verbose_name_plural = '排机管理'

    def __str__(self):
        return '%s' % self.name


class SampleManage(models.Manager):
    def sample_count(self, keyword):
        return self.filter(project=keyword).count()


class Sample(models.Model):
    """
    Sample class
    """
    name = models.CharField('样品名称', max_length=15, help_text='最大只允许15个字符')
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name='项目名',
    )
    experiment_num = models.PositiveSmallIntegerField('实验次数', default=0)
    contract_data = models.PositiveIntegerField('合同数据量')
    objects = SampleManage()

    class Meta:
        verbose_name = '样品管理'
        verbose_name_plural = '样品管理'

    def __str__(self):
        return '%s' % self.name


class SequenceInfo(models.Model):
    """
    Sequence class
    """
    library = models.ForeignKey(
        Library,
        on_delete=models.CASCADE,
        verbose_name='文库名',
    )
    sample = models.ForeignKey(
        Sample,
        on_delete=models.CASCADE,
        verbose_name='样品名',
    )
    primer = models.ForeignKey(
        'lims.Primer',
        on_delete=models.CASCADE,
        verbose_name='类型',
    )
    index = models.ForeignKey(
        'lims.Barcode',
        on_delete=models.CASCADE,
        verbose_name='index号',
    )
    apply_data = models.PositiveIntegerField('排机量')

    class Meta:
        verbose_name = '排机信息'
        verbose_name_plural = '排机信息'

    def __str__(self):
        return '%s' % self.sample
