#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@author  :   Charles Lai
@file    :   pagination.py
@time    :   2023/03/26 15:22
@contact :   qqing_lai@hotmail.com
'''

# here put the import lib
# import math
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.response import Response
from rest_framework import status


class CustomPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        # print('pages total', self.paginator.num_pages)
        # print('page size', self.page_size, 'totalPage', self.page.paginator.num_pages)
        return Response({'data': {'list': data, 'total': self.page.paginator.count, 'next': self.get_next_link(),
                                  'previous': self.get_previous_link()}, 'code': 20000, 'message': None}, status=status.HTTP_200_OK)
