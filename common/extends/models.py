#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@author  :   Charles Lai
@file    :   models.py
@time    :   2023/03/26 12:59
@contact :   qqing_lai@hotmail.com
'''

# here put the import lib
from django.db import models


class TimeAbstract(models.Model):
    update_time = models.DateTimeField(
        auto_now=True, null=True, blank=True, verbose_name='更新时间')
    created_time = models.DateTimeField(
        auto_now_add=True, null=True, blank=True, verbose_name='创建时间')

    class ExtMeta:
        related = False
        dashboard = False

    class Meta:
        abstract = True
        ordering = ['-id']


class CommonParent(models.Model):
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name='children')

    class Meta:
        abstract = True
