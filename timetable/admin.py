from django.contrib import admin

# Register your models here.
from .models import Schedule, Stack

admin.site.register(Schedule)
admin.site.register(Stack)
