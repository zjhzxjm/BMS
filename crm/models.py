from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    """
    Customer class
    """
    name = models.CharField('客户名', max_length=12, help_text='最大只允许12个字符')
    organization = models.CharField('单位', max_length=40, help_text='最大只允许40个字符')
    email = models.EmailField('邮箱')
    phone = models.PositiveIntegerField('手机')
    call = models.PositiveIntegerField('电话')
    address = models.CharField('地址', max_length=50, help_text='最大只允许50个字符')
    linker = models.ForeignKey(User)

    class Meta:
        verbose_name = "客户管理"
        verbose_name_plural = "客户管理"

    def __str__(self):
        return "%s" % self.name
