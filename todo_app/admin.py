from django.contrib import admin
from .models import Label, Status, List, Task

admin.site.register(Label)
admin.site.register(Status)
admin.site.register(List)
admin.site.register(Task)
