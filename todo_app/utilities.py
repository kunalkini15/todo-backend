from .models import Task, List, Subscription, Label, Status
from todolist.settings import EMAIL_HOST_USER
from django.core.mail import send_mail


def get_lists(subscribed_user):
    return List.objects.filter(user=subscribed_user.user)

def get_active_tasks(list_obj):
    return Task.objects.filter(list_obj=list_obj).filter(isCompleted=False)

def send_reminder_email(user, task_due):
    subject = "Reminder of tasks"
    message = ("Hi " + user.first_name + ",\n" "We here at todo tracker want you to be as productive as possible. "
                 "Here are some of the tasks that you are yet to finish.\n")
    for i in range(min(3, len(task_due))):
        message += str((i+1)) + ". " + task_due[i]["task_name"] + " Due On " + str(task_due[i]["task_due_on"]) + "\n"
    message += "\nLog in to todo-tracker now and complete the tasks."

    message += "\n\n"

    message += "Regards,\nTeam TODO tracker"


    send_mail(subject, message,  EMAIL_HOST_USER,
        [user.email],
         fail_silently=False)
