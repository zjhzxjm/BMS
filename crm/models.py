from django.db import models
from django.contrib.auth.models import User
from datetime import date


class Customer(models.Model):
    """
    客户管理模型
    """
    LEVEL_CHOICES = (
        (1, '一般'),
        (2, '重要'),
        (3, '非常重要'),
    )
    name = models.CharField('客户姓名', max_length=12)
    organization = models.CharField('单位（全称）', max_length=20)
    department = models.CharField('院系/科室（全称）', max_length=20)
    address = models.CharField('办公地址', max_length=50)
    title = models.CharField('职务', max_length=50)
    contact = models.PositiveIntegerField('联系方式')
    email = models.EmailField('邮箱')
    level = models.IntegerField(
        '客户分级',
        choices=LEVEL_CHOICES,
        default=1,
    )
    linker = models.ForeignKey(User, verbose_name='联络人')

    class Meta:
        verbose_name = "客户管理"
        verbose_name_plural = "客户管理"

    def __str__(self):
        return "%s" % self.name


class Intention(models.Model):
    """
    意向管理模型
    """
    TYPE_CHOICES = (
        (1, '16S/ITS'),
        (2, '宏基因组'),
        (3, '单菌'),
        (4, '转录组'),
        (5, '其它'),
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        verbose_name='客户',
    )
    project_name = models.CharField('项目名称', max_length=50)
    project_type = models.IntegerField(
        '项目类型',
        choices=TYPE_CHOICES,
        default=1
    )
    amount = models.IntegerField('数量')
    closing_date = models.DateField('预计成交时间', default=date.today())
    price = models.DecimalField('预计成交价', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "意向管理"
        verbose_name_plural = "意向管理"

    def __str__(self):
        return "%s" % self.project_name


class IntentionRecord(models.Model):
    intention = models.ForeignKey(
        Intention,
        verbose_name='意向项目'
    )
    status = models.CharField('进展/状态', max_length=15)
    record_date = models.DateField('跟进时间', default=date.today())
    note = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '进展记录'
        verbose_name_plural = '进展记录'

    def __str__(self):
        return '%s-%s' % (self.status, self.record_date)
