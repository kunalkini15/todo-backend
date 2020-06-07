import datetime

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

    message += "\nLog in to TODO-Tracker - (https://to-do-tracking-made-easy.web.app/) now and complete the tasks.\n\nRegards,\nTeam TODO tracker"

    send_mail(subject, message,  EMAIL_HOST_USER,
        [user.email],
         fail_silently=False)

def get_report(user):
    lists = List.objects.filter(user=user)
    total_tasks, completed_tasks, late_tasks, active_tasks, total_task_till_today = 0, 0, 0, 0, 0
    for list_obj in lists:
        total_tasks += Task.objects.filter(list_obj = list_obj).count()
        completed_tasks += Task.objects.filter(list_obj = list_obj).filter(isCompleted=True).count()
        late_tasks += Task.objects.filter(list_obj = list_obj).filter(isCompleted=False).filter(due_date__lt =  datetime.datetime.now()).count()
        active_tasks += Task.objects.filter(list_obj = list_obj).filter(isCompleted=False).count()

    return total_tasks, completed_tasks, late_tasks, active_tasks


def send_report_email(user):
    total_tasks, completed_tasks, late_tasks, active_tasks = get_report(user)

    subject = "To-do Progress report"
    message = ("Hi " + user.first_name + ",\n"
                    "Here is your progress report so far.\n")
    message += ("\nTotal tasks you have created till date: %s\nNumber of completed tasks: %s\n"
                    "Number of incomplete tasks: %s\nNumber of overdue tasks: %s\n"%(total_tasks, completed_tasks, active_tasks, late_tasks))
    if total_tasks == 0:
        to_do_score = 0
    else:
        to_do_score = int(completed_tasks / total_tasks * 100)

    message += "Your to-do score is: %s"%(to_do_score)

    message += "\nLog in to TODO-Tracker - (https://to-do-tracking-made-easy.web.app/) now and complete the tasks to improve your to-do score.\n\nRegards,\nTeam TODO tracker"

    send_mail(subject, message,  EMAIL_HOST_USER,
        [user.email],
         fail_silently=False)
