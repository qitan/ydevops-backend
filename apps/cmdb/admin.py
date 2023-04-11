from django.contrib import admin

# Register your models here.
from .models import Region, Idc

admin.site.register(Region)
admin.site.register(Idc)
