#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@author  :   Charles Lai
@file    :   models.py
@time    :   2023/03/26 12:16
@contact :   qqing_lai@hotmail.com
'''

# here put the import lib
from django.db import models
from django.contrib.auth.models import AbstractUser

from common.extends.models import TimeAbstract, CommonParent

# Create your models here.


def org_extra_data():
    return {
        'leader_user_id': '',  # 存储部门领导ID
        'dn': '',  # 存储ldap dn
    }


def user_extra_data():
    return {
        'ding_userid': '',  # 钉钉用户ID
        'feishu_userid': '',  # 飞书UserID
        'feishu_unionid': '',  # 飞书UnionID
        'feishu_openid': '',  # 飞书OpenID
        'leader_user_id': '',  # 直属领导ID
        'dn': '',  # ldap dn
    }


class DataDict(CommonParent):
    key = models.CharField(max_length=80, unique=True, verbose_name='键')
    value = models.CharField(max_length=80, verbose_name='值')
    extra = models.TextField(null=True, blank=True,
                             default='', verbose_name='额外参数')
    desc = models.CharField(max_length=255, blank=True,
                            null=True, verbose_name='备注')

    def __str__(self):
        return self.value

    class Meta:
        default_permissions = ()
        verbose_name = '字典'
        verbose_name_plural = verbose_name + '管理'


class Menu(TimeAbstract, CommonParent):
    """
    菜单模型
    """
    name = models.CharField(max_length=30, unique=True, verbose_name='菜单名')
    title = models.CharField(max_length=30, null=True,
                             blank=True, verbose_name='菜单显示名')
    icon = models.CharField(max_length=50, null=True,
                            blank=True, verbose_name='图标')
    path = models.CharField(max_length=158, null=True,
                            blank=True, verbose_name='路由地址')
    redirect = models.CharField(
        max_length=200, null=True, blank=True, verbose_name='跳转地址')
    is_frame = models.BooleanField(default=False, verbose_name='外部菜单')
    hidden = models.BooleanField(default=False, verbose_name='是否隐藏')
    spread = models.BooleanField(default=False, verbose_name='是否默认展开')
    sort = models.IntegerField(default=0, verbose_name='排序标记')
    component = models.CharField(
        max_length=200, default='Layout', verbose_name='组件')
    affix = models.BooleanField(default=False, verbose_name='固定标签')
    single = models.BooleanField(default=False, verbose_name='标签单开')
    activeMenu = models.CharField(
        max_length=128, blank=True, null=True, verbose_name='激活菜单')

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = ()
        verbose_name = '菜单'
        verbose_name_plural = verbose_name + '管理'
        ordering = ['id']


class Permission(TimeAbstract, CommonParent):
    """
    权限模型
    """
    name = models.CharField(max_length=30, unique=True, verbose_name='权限名')
    method = models.CharField(max_length=50, null=True,
                              blank=True, verbose_name='方法')

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = ()
        verbose_name = '权限'
        verbose_name_plural = verbose_name + '管理'


class Role(TimeAbstract):
    """
    角色模型
    """
    name = models.CharField(max_length=32, unique=True, verbose_name='角色')
    permissions = models.ManyToManyField(
        Permission, blank=True, related_name='role_permission', verbose_name='权限')
    menus = models.ManyToManyField(Menu, blank=True, verbose_name='菜单')
    desc = models.CharField(max_length=50, blank=True,
                            null=True, verbose_name='描述')

    def __str__(self):
        return self.name

    class Meta:
        default_permissions = ()
        verbose_name = '角色'
        verbose_name_plural = verbose_name + '管理'


class Organization(TimeAbstract, CommonParent):
    """
    组织架构
    """
    organization_type_choices = (
        ('company', '公司'),
        ('department', '部门')
    )
    dept_id = models.CharField(max_length=32, unique=True, verbose_name='部门ID')
    name = models.CharField(max_length=60, verbose_name='名称')
    type = models.CharField(
        max_length=20, choices=organization_type_choices, default='department', verbose_name='类型')
    extra_data = models.JSONField(
        default=org_extra_data, verbose_name='其它数据', help_text=f'数据格式：{org_extra_data()}')

    @property
    def full(self):
        l = []
        self.get_parents(l)
        return l

    def get_parents(self, parent_result: list):
        if not parent_result:
            parent_result.append(self)
        parent_obj = self.parent
        if parent_obj:
            parent_result.append(parent_obj)
            parent_obj.get_parents(parent_result)

    def __str__(self):
        return self.name

    class ExtMeta:
        related = True
        dashboard = False

    class Meta:
        default_permissions = ()
        verbose_name = '组织架构'
        verbose_name_plural = verbose_name + '管理'


class UserProfile(TimeAbstract, AbstractUser):
    """
    用户信息
    """
    mobile = models.CharField(max_length=11, null=True,
                              blank=True, verbose_name='手机号码')
    avatar = models.ImageField(upload_to='static/%Y/%m', default='image/default.png',
                               max_length=250, null=True, blank=True)
    department = models.ManyToManyField(
        Organization, related_name='org_user', verbose_name='部门')
    # 职能：根据职能授权
    position = models.CharField(
        max_length=50, null=True, blank=True, verbose_name='职能')
    # 职位：仅展示用户title信息
    title = models.CharField(max_length=50, null=True,
                             blank=True, verbose_name='职位')
    roles = models.ManyToManyField(
        Role, verbose_name='角色', related_name='user_role', blank=True)
    extra_data = models.JSONField(
        default=user_extra_data, verbose_name='其它数据', help_text=f'数据格式：{user_extra_data()}')
    is_ldap = models.BooleanField(default=False, verbose_name='是否ldap用户')

    @property
    def nickname(self):
        if self.first_name:
            return self.first_name
        return self.username

    def __str__(self):
        return self.name

    class ExtMeta:
        related = True
        dashboard = False
        icon = 'peoples'

    class Meta:
        default_permissions = ()
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name + '管理'
        ordering = ['id']
