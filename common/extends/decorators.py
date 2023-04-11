#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@author  :   Charles Lai
@file    :   decorators.py
@time    :   2023/03/23 21:41
@contact :   qqing_lai@hotmail.com
'''

# here put the import lib
from functools import wraps

from rest_framework.response import Response

from cmdb.models import MicroApp

from common.extends.viewsets import ops_response


def cmdb_app_unique_check():
    """
    应用唯一性检查

    appid: {product.name}.{app.name}
    """

    def check_app(product, name):
        try:
            if MicroApp.objects.filter(project__product__id=product, name=name).exists():
                # 存在应用
                return True
        except BaseException as e:
            pass
        return False

    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if check_app(request.data['product'], request.data['name']):
                return ops_response({}, success=False, errorCode=40300, errorMessage=f'该产品下已存在[{request.data["name"]}]同名应用.')

            return func(self, request, *args, **kwargs)

        return wrapper

    return decorator
