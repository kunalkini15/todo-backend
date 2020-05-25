from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
class Label(models.Model):
    name = models.CharField(max_length=30)
    def __str__(self):
        return self.name

class Status(models.Model):
    status = models.CharField(max_length=30)

    def __str__(self):
        return self.status

class Task(models.Model):

    name = models.CharField(max_length = 30)
    description = models.TextField()
    start_date = models.DateTimeField(default=timezone.now())
    due_date = models.DateTimeField()
    list_obj = models.ForeignKey('List', on_delete=models.CASCADE, null = True)
    label = models.ForeignKey('Label', null=True, blank=True, on_delete=models.CASCADE)
    status = models.ForeignKey('Status', null=True, blank=True, on_delete=models.CASCADE)
    isCompleted = models.BooleanField(default=False)
    def __str__(self):
        return str(self.name)

class List(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=30)
    description = models.TextField()
    tasks = models.ManyToManyField('Task')

    def __str__(self):
        return self.name
