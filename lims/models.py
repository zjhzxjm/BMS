from django.db import models
from django.contrib.auth.models import User
from pm.models import Project


class IsExtManager(models.Manager):
    # 返回通过核对且需提取的样品
    def get_queryset(self):
        return super(IsExtManager, self).get_queryset().filter(project__is_confirm=True).filter(check=True)\
            .filter(project__is_ext=True)


class IsQcManager(models.Manager):
    # 返回通过项目确认、样品核对且需质检的样品
    def get_queryset(self):
        return super(IsQcManager, self).get_queryset().filter(project__is_confirm=True).filter(check=True)\
            .filter(project__is_qc=True)


class IsLibManager(models.Manager):
    # 返回通过核对且需建库的样品
    def get_queryset(self):
        return super(IsLibManager, self).get_queryset().filter(project__is_confirm=True).filter(check=True)\
            .filter(project__is_lib=True)


class SampleInfo(models.Model):
    project = models.ForeignKey(
        'pm.Project',
        verbose_name='项目',
        on_delete=models.CASCADE,
    )
    type = models.CharField('样品类型', max_length=20)
    species = models.CharField('物种', max_length=20)
    name = models.CharField('样品名称', max_length=50)
    volume = models.DecimalField('体积uL', max_digits=5, decimal_places=3)
    concentration = models.DecimalField('浓度ng/uL', max_digits=5, decimal_places=3)
    receive_date = models.DateField('收样日期')
    check = models.NullBooleanField('样品核对', null=True)
    note = models.TextField('备注', blank=True, null=True)

    objects = models.Manager()
    is_ext_objects = IsExtManager()
    is_qc_objects = IsQcManager()
    is_lib_objects = IsLibManager()

    class Meta:
        unique_together = ('project', 'name', 'receive_date')
        verbose_name = '0样品管理'
        verbose_name_plural = '0样品管理'

    def __str__(self):
        return '%s %s  [%s]' % (self.project, self.name, self.receive_date)


class ExtTask(models.Model):
    sample = models.ForeignKey(
        SampleInfo,
        verbose_name='样品',
        on_delete=models.CASCADE,
    )
    sub_date = models.DateField('下单日期')
    date = models.DateField('提取日期', null=True)
    staff = models.ForeignKey(
        User,
        verbose_name='实验员',
        null=True
    )
    result = models.NullBooleanField('结论', null=True)
    note = models.TextField('备注', blank=True, null=True)

    class Meta:
        verbose_name = '1提取实验'
        verbose_name_plural = '1提取实验'

    def __str__(self):
        return '%s' % self.result


class QcTask(models.Model):
    RESULTS_CHOICES = (
        (0, '待质检'),
        (1, '合格'),
        (2, '不合格（可风险建库）'),
        (3, '不合格（不可风险建库）'),
    )
    sample = models.ForeignKey(
        SampleInfo,
        verbose_name='样品',
        on_delete=models.CASCADE,
    )
    sub_date = models.DateField('下单日期')
    date = models.DateField('质检日期', null=True)
    staff = models.ForeignKey(
        User,
        verbose_name='实验员',
        null=True
    )
    volume = models.DecimalField('体积uL', max_digits=5, decimal_places=3, null=True)
    concentration = models.DecimalField('浓度ng/uL', max_digits=5, decimal_places=3, null=True)
    total = models.DecimalField('总量ng', max_digits=5, decimal_places=3, null=True)
    result = models.IntegerField(
        '结论',
        choices=RESULTS_CHOICES,
        null=True,
    )
    note = models.TextField('备注', blank=True, null=True)

    class Meta:
        verbose_name = '2样品质检'
        verbose_name_plural = '2样品质检'

    def __str__(self):
        return '%s' % self.result


class LibTask(models.Model):
    sample = models.ForeignKey(
        SampleInfo,
        verbose_name='样品',
        on_delete=models.CASCADE,
    )
    sub_date = models.DateField('下单日期')
    date = models.DateField('建库日期', null=True)
    staff = models.ForeignKey(
        User,
        verbose_name='实验员',
        null=True
    )
    type = models.CharField('文库类型', max_length=20, null=True)
    sample_code = models.CharField('样品编号', max_length=20, null=True)
    lib_code = models.CharField('文库号', max_length=20, null=True)
    index = models.CharField('Index', max_length=20, null=True)
    length = models.PositiveIntegerField('文库大小bp', null=True)
    volume = models.DecimalField('体积uL', max_digits=5, decimal_places=3, null=True)
    concentration = models.DecimalField('浓度ng/uL', max_digits=5, decimal_places=3, null=True)
    total = models.DecimalField('总量ng', max_digits=5, decimal_places=3, null=True)
    result = models.NullBooleanField('结论', null=True)
    note = models.TextField('备注', blank=True, null=True)

    class Meta:
        verbose_name = '3样品建库'
        verbose_name_plural = '3样品建库'

    def __str__(self):
        return '%s' % self.result





