from django.db import models


class Invoice(models.Model):
    invoice = models.OneToOneField(
        'mm.Invoice',
        verbose_name='发票',
    )
    invoice_code = models.CharField('发票单号', max_length=12)
    date = models.DateTimeField('开票时间', null=True)

    class Meta:
        verbose_name = '发票管理'
        verbose_name_plural = '发票管理'

    def __str__(self):
        return '%s' % self.invoice_code


class Bill(models.Model):
    invoice = models.ForeignKey(Invoice, verbose_name='发票')
    income = models.DecimalField('到账金额', max_digits=9, decimal_places=2)
    date = models.DateTimeField('到账时间')

    class Meta:
        verbose_name = '进账管理'
        verbose_name_plural = '进帐管理'

    def __str__(self):
        return '%f' % self.income
