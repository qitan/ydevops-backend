#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@author  :   Charles Lai
@file    :   view_assets.py
@time    :   2023/03/21 22:21
@contact :   qqing_lai@hotmail.com
'''

# here put the import lib
from rest_framework.response import Response

from cmdb.models import Region, Idc
from cmdb.serializer import RegionSerializers, IdcSerializers

from common.extends.viewsets import AutoModelViewSet


class RegionViewSet(AutoModelViewSet):
    """
    区域视图

    ### 区域权限
        {'*': ('env_all', '区域环境管理')},
        {'get': ('env_list', '查看区域环境')},
        {'post': ('env_create', '创建区域环境')},
        {'put': ('env_edit', '编辑区域环境')},
        {'patch': ('env_edit', '编辑区域环境')},
        {'delete': ('env_delete', '删除区域环境')}
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('env_all', '区域环境管理')},
        {'get': ('env_list', '查看区域环境')},
        {'post': ('env_create', '创建区域环境')},
        {'put': ('env_edit', '编辑区域环境')},
        {'patch': ('env_edit', '编辑区域环境')},
        {'delete': ('env_delete', '删除区域环境')}
    )
    queryset = Region.objects.all()
    serializer_class = RegionSerializers


class IdcViewSet(AutoModelViewSet):
    """
    IT资产 - IDC视图

    ### IDC权限
        {'*': ('itasset_all', 'IT资产管理')},
        {'get': ('itasset_list', '查看IT资产')},
        {'post': ('itasset_create', '创建IT资产')},
        {'put': ('itasset_edit', '编辑IT资产')},
        {'delete': ('itasset_delete', '删除IT资产')}
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('itasset_all', 'IT资产管理')},
        {'get': ('itasset_list', '查看IT资产')},
        {'post': ('itasset_create', '创建IT资产')},
        {'put': ('itasset_edit', '编辑IT资产')},
        {'delete': ('itasset_delete', '删除IT资产')}
    )
    queryset = Idc.objects.all()
    serializer_class = IdcSerializers
