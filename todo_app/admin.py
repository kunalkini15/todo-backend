from django.contrib import admin
from .models import Label, Status, List, Task, Subscription

admin.site.register(Label)
admin.site.register(Status)
admin.site.register(List)
admin.site.register(Task)
admin.site.register(Subscription)
