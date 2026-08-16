from django.contrib import admin

from .models import Label, Status, Task

admin.site.register(Status)
admin.site.register(Label)
admin.site.register(Task)
