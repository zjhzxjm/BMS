from django.db import models
from django.contrib.auth.models import User


class Contract(models.Model):
    RANGE_CHOICES = (
        (1, '高于销售底价'),
        (2, '总监底价'),
        (3, '低于总监底价'),
    )
    TYPE_CHOICES = (
        (1, '16S/ITS'),
        (2, '宏基因组'),
        (3, '单菌'),
        (4, '转录组'),
        (5, '其它'),
    )
    contract_number = models.CharField('合同号', max_length=15, unique=True)
    name = models.CharField('合同名', max_length=100)
    type = models.IntegerField(
        '类型',
        choices=TYPE_CHOICES,
    )
    salesman = models.ForeignKey(User, verbose_name='业务员')
    price = models.DecimalField('单价', max_digits=7, decimal_places=2)
    range = models.IntegerField(
        '价格区间',
        choices=RANGE_CHOICES,
    )
    fis_amount = models.DecimalField('首款额', max_digits=12, decimal_places=2)
    fis_date = models.DateField('首款到款日', blank=True, null=True)
    fin_amount = models.DecimalField('尾款额', max_digits=12, decimal_places=2)
    fin_date = models.DateField('尾款到款日', blank=True, null=True)
    send_date = models.DateField('合同寄出日', null=True)
    tracking_number = models.CharField('快递单号', max_length=15, blank=True)
    receive_date = models.DateField('合同寄到日', null=True)
    contract_file = models.FileField('附件', upload_to='uploads/%Y/%m')

    class Meta:
        verbose_name = '合同管理'
        verbose_name_plural = '合同管理'

    def file_link(self):
        if self.contract_file:
            return "<a href='%s'>下载</a>" % (self.contract_file.url,)
        else:
            return "未上传"
    file_link.short_description = "附件"
    file_link.allow_tags = True

    def __str__(self):
        return '%s' % self.contract_number


class Invoice(models.Model):
    PERIOD_CHOICES = (
        ('FIS', '首款'),
        ('FIN', '尾款'),
    )
    contract = models.ForeignKey(
        Contract,
        verbose_name='合同',
        on_delete=models.CASCADE,
    )
    title = models.CharField('发票抬头', max_length=25)
    period = models.CharField('款期', max_length=3, choices=PERIOD_CHOICES, default='FIS')
    amount = models.DecimalField('开票金额', max_digits=9, decimal_places=2)
    note = models.TextField('备注')
    submit = models.NullBooleanField('提交开票', null=True)

    class Meta:
        verbose_name = '开票申请'
        verbose_name_plural = '开票申请'

    def __str__(self):
        return '%.2f' % self.amount



