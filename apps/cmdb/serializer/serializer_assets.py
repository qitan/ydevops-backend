#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@author  :   Charles Lai
@file    :   serializer_assets.py
@time    :   2023/03/21 22:18
@contact :   qqing_lai@hotmail.com
'''

# here put the import lib
from rest_framework import serializers

from cmdb.models import Region, Idc


class RegionSerializers(serializers.ModelSerializer):

    class Meta:
        model = Region
        fields = '__all__'


class IdcSerializers(serializers.ModelSerializer):

    class Meta:
        model = Idc
        fields = '__all__'
