import datetime
from datetime import timedelta


from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core import serializers

from .models import List, Label, Task, Status, Subscription
from .utilities import get_lists, get_active_tasks, send_reminder_email, get_report, send_report_email

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from todolist.settings import EMAIL_HOST_USER
from django.core.mail import send_mail

from background_task import background


class Register(APIView):
    def post(self, request):
        name = request.data["name"]
        email = request.data["email"]
        password = request.data["password"]

        try:
            user = User.objects.get(email=email)
            return Response("User with this email already exists", status=status.HTTP_409_CONFLICT)
        except:
            user = User.objects.create_user(first_name=name, username=email, email=email, password=password)
            user.save()

        return Response("User created successfully", status=status.HTTP_201_CREATED)

class Login(APIView):
    def post(self, request):
        email = request.data["email"]
        password = request.data["password"]
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(username=email, password=password)
            if user is not None:
                try:
                    sub = Subscription.objects.get(user=user)
                    data={
                        "message": "User Logged in successfully",
                        "subscribed": True,
                        "name": user.first_name
                    }
                    return Response(data, status=status.HTTP_200_OK)
                except:
                    data={
                        "message": "User Logged in successfully",
                        "subscribed": False,
                        "name": user.first_name
                    }
                    return Response(data, status=status.HTTP_200_OK)
            else:
                return Response("You have entered the wrong password, Please try again!!", status=status.HTTP_401_UNAUTHORIZED)
        except:
            return Response("User with this email doesn't exist", status=status.HTTP_404_NOT_FOUND)

class ListView(APIView):
    def get(self, request):
        try:

            email = request.GET["email"]
            user = User.objects.get(email=email)
            list_objects = List.objects.filter(user=user)
            response =[]
            for list_object in list_objects:
                response.append({
                    "id": list_object.id,
                    "name":list_object.name,
                })
            return JsonResponse(response, safe=False)
        except:
            return Response("Error while fetching lists", status=status.HTTP_503_SERVICE_UNAVAILABLE)



    def post(self, request):

        try:
            name = request.data["name"]
            description = request.data["description"]
            email = request.data["email"]

            user = User.objects.get(email=email)


            list_obj = List.objects.create(user=user, name=name, description=description)
            return Response("List created successfully", status=status.HTTP_201_CREATED)
        except:

            return Response("Something went wrong", status=status.HTTP_409_CONFLICT)

    def delete(self, request):
        try:
            id = request.data["id"]
            list_obj = List.objects.get(pk=id)
            list_obj.delete()
            return JsonResponse("List deleted successfully", safe=False)
        except:
            return Response("Error while deleting the list", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TaskView(APIView):

    def get(self, request, task_id=0):

        try:
            if task_id == 0:
                list_id = request.GET["id"]

                tasks = Task.objects.filter(list_obj=List.objects.get(pk=list_id))

                # applying filters
                try:
                    progress = request.GET["progress"]
                    progress_filter = True
                except:
                    progress = "active"
                    progress_filter=True

                try:
                    label = request.GET["label"]
                    label_filter = True
                except:
                    label_filter=False

                try:
                    task_status = request.GET["status"]
                    status_filter = True
                except:
                    status_filter=False

                try:
                    priority = request.GET["priority"]
                    priority_filter = True
                except:
                    priority_filter=False



                if progress_filter: # applying progress filters
                    if progress == "Completed":
                        filter=True
                    else:
                        filter=False
                    tasks = tasks.filter(isCompleted=filter)

                if label_filter:
                    try:
                        label_obj = Label.objects.get(name=label)
                    except:
                        label_obj = Label.objects.create(name=label)
                    tasks = tasks.filter(label=label_obj)

                if status_filter:
                    try:
                        status_obj = Status.objects.get(status=task_status)
                    except:
                        status_obj = Status.objects.create(status=task_status)
                    tasks = tasks.filter(status=status_obj)

                # add priority filter here
                if priority_filter:
                    if priority == "Today":
                        priority_date = datetime.date.today()
                        tasks = tasks.filter(due_date__date = priority_date)

                    elif priority == "Week":
                        start = datetime.date.today()
                        end = datetime.date.today() + timedelta(7)

                        tasks = tasks.filter(due_date__date__gte = start, due_date__date__lte=end)



                response = []
                for task in tasks:
                    current_task_object = {
                    "id": task.id,
                    "name": task.name,
                    "description": task.description,
                    "start_date": task.start_date,
                    "due_date": task.due_date,
                    "label": task.label.name,
                    "status": task.status.status,
                    "isCompleted": task.isCompleted
                    }
                    response.append(current_task_object)
                return JsonResponse(response, safe=False)
            else:
                task = Task.objects.get(pk=task_id)
                current_task_object = {
                    "id": task.id,
                    "name": task.name,
                    "description": task.description,
                    "start_date": task.start_date,
                    "due_date": task.due_date,
                    "label": task.label.name,
                    "status": task.status.status,
                    "isCompleted": task.isCompleted
                }
                return JsonResponse(current_task_object)

        except:
            return Response("Error while fetching tasks", status=status.HTTP_503_SERVICE_UNAVAILABLE)



    def post(self, request):
        try:
            list_id = request.data["id"]
            name = request.data["name"]
            description = request.data["description"]
            label = request.data["label"]
            task_status = request.data["status"]
            task_date = request.data["date"]
            task_time = request.data["time"]
            split_date = list(map(int, task_date.split("-")))
            split_time = list(map(int, task_time.split(":")))
            due_date = (datetime.datetime(split_date[0], split_date[1], split_date[2], split_time[0], split_time[1]))
            list_obj = List.objects.get(id=list_id)

            try:
                label_obj = Label.objects.get(name=label)
            except:
                label_obj = Label.objects.create(name=label)

            try:
                status_obj = Status.objects.get(status=task_status)
            except:
                status_obj = Status.objects.create(status=task_status)

            task_obj = Task.objects.create(name=name, description=description, due_date=due_date,
                                            list_obj=list_obj, label=label_obj, status=status_obj
                                            )


            return Response("Task created successfully", status=status.HTTP_201_CREATED)
        except:
            return Response("Something went wrong", status=status.HTTP_409_CONFLICT)


    def put(self, request):
        try:

            task_id = request.data["id"]
            task_obj = Task.objects.get(pk=task_id)
            if "name" in request.data:
                task_obj.name = request.data["name"]
            if "description" in request.data:
                task_obj.description = request.data["description"]

            if "label" in request.data:
                try:
                    label_obj = Label.objects.get(name=label)
                except:
                    label_obj = Label.objects.create(name=label)
                task_obj.label =label_obj

            if "status" in request.data:
                try:
                    status_obj = Status.objects.get(status=task_status)
                except:
                    status_obj = Status.objects.create(status=task_status)
                task_obj.status = status_obj

            if "date" in request.data and "time" in request.data:
                task_date = request.data["date"]
                task_time = request.data["time"]
                split_date = list(map(int, task_date.split("-")))
                split_time = list(map(int, task_time.split(":")))
                due_date = (datetime.datetime(split_date[0], split_date[1], split_date[2], split_time[0], split_time[1]))
                task_obj.due_date = due_date
            if "isCompleted" in request.data:
                task_obj.isCompleted = request.data["isCompleted"]
            task_obj.save()

            return JsonResponse("Task Updated successfully", safe=False)
        except:
            return Response("Can't update the task at this moment", status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def delete(self, request):
        try:
            task_id = int(request.data["id"])
            try:
                t = Task.objects.get(pk=task_id)
                t.delete()
                return JsonResponse("Deleted successfully", safe=False)
            except:
                return Response("Task Not found", status=status.HTTP_404_NOT_FOUND)
        except:
            return Response("Something went wrong!", status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class SubscriptionView(APIView):
    def get(self, request):
        users = Subscription.objects.all()
        response = []
        for user in users:
            response.append({
                "name": user.user.name,
                "email": user.user.email
            })

        return JsonResponse(response, safe=False)

    def post(self, request):
        email = request.data["email"]
        subscribe = request.data["subscribe"]
        if subscribe:
            try:
                send_email(repeat=43200, repeat_until=datetime.datetime(2020, 7, 31, 8, 0))
                user = Subscription.objects.get(user=User.objects.get(email=email))
                return JsonResponse("User is already subscribed", safe=False)
            except:
                user = Subscription.objects.create(user=User.objects.get(email=email))
                return JsonResponse("User subscribed suceessfully", safe=False)
        else:
            try:
                user = Subscription.objects.get(user=User.objects.get(email=email))
                user.delete()
                return JsonResponse("User unsubscribed successfully", safe=False)
            except:
                return JsonResponse("User unsubscribed successfully", safe=False)



@background(schedule=datetime.datetime(2020, 6, 7, 20, 0))
def send_email():
    subscribed_users = Subscription.objects.all()
    response = []
    for subscribed_user in subscribed_users:
        lists = get_lists(subscribed_user)
        task_due = []
        for list_obj in lists:
            tasks = get_active_tasks(list_obj)
            for task in tasks:
                task_due.append({
                    "task_name": task.name,
                    "task_due_on": task.due_date
                })

        send_reminder_email(subscribed_user.user, task_due)
    return JsonResponse("Done", safe=False)


def call_background_email_service(request):
    send_email(repeat=43200, repeat_until=datetime.datetime(2020, 7, 31, 8, 0))
    return JsonResponse("Done", safe=False)

class UserView(APIView):
    def delete(self, request):
        email = request.data["email"]
        user = User.objects.get(email=email)
        user.delete()
        return JsonResponse("User deleted successfully", safe=False)

class PerformanceView(APIView):
    def get(self, request):
        user = User.objects.get(email =  request.GET["email"])
        total_tasks, completed_tasks, late_tasks, active_tasks = get_report(user)
        response = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "late_tasks": late_tasks,
            "active_tasks": active_tasks
        }

        return JsonResponse(response)

def send_report_via_email(request):
    user = User.objects.get(email =  request.GET["email"])
    send_report_email(user)

    return JsonResponse("Email sent successfully", safe=False)
