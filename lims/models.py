from django.db import models


class Primer(models.Model):
    """
    Primer class
    """
    name = models.CharField('引物名称', max_length=20, help_text='最大只允许20个字符')
    forward_primer = models.CharField('正向序列', max_length=50, help_text='最大只允许50个字符')
    reverse_primer = models.CharField('反向序列', max_length=50, help_text='最大只允许50个字符')

    class Meta:
        verbose_name = '引物管理'
        verbose_name_plural = '引物管理'

    def __str__(self):
        return '%s' % self.name


class Barcode(models.Model):
    """
    Barcode class
    """
    name = models.CharField("Barcode名", max_length=15)
    sequence = models.CharField("序列", max_length=20)

    class Meta:
        verbose_name = "Barcode管理"
        verbose_name_plural = "Barcode管理"

    def __str__(self):
        return "%s" % self.name
