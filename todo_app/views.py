import datetime

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core import serializers

from .models import List, Label, Task, Status, Subscription
from .utilities import get_lists, get_active_tasks, send_reminder_email

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
            return Response("User already exists", status=status.HTTP_409_CONFLICT)
        except:
            user = User.objects.create_user(first_name=name, username=email, email=email, password=password)
            user.save()

        return Response("User created successfully", status=status.HTTP_201_CREATED)

class Login(APIView):
    def post(self, request):
        email = request.data["email"]
        password = request.data["password"]
        try:
            user = authenticate(username=email, password=password)
            if user is not None:
                try:
                    sub = Subscription.objects.get(user=user)
                    data={
                        "message": "User Logged in successfully",
                        "subscribed": True
                    }
                    print(data)
                    return Response(data, status=status.HTTP_200_OK)
                except:
                    data={
                        "message": "User Logged in successfully",
                        "subscribed": False
                    }
                    print(data)
                    return Response(data, status=status.HTTP_200_OK)
            else:
                return Response("Wrong password", status=status.HTTP_401_UNAUTHORIZED)
        except:
            return Response("User doesn't exist", status=status.HTTP_404_NOT_FOUND)

class ListView(APIView):
    def get(self, request):
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



    def post(self, request):
        name = request.data["name"]
        description = request.data["description"]
        email = request.data["email"]

        user = User.objects.get(email=email)


        list_obj = List.objects.create(user=user, name=name, description=description)

        return Response("List created successfully", status=status.HTTP_201_CREATED)



class TaskView(APIView):

    def get(self, request, task_id=0):
        if task_id == 0:
            list_id = request.GET["id"]

            for i in request.GET:
                print(i, request.GET[i])
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
                label_obj = Label.objects.get(name=label)
                tasks = tasks.filter(label=label_obj)

            if status_filter:
                status_obj = Status.objects.get(status=task_status)
                tasks = tasks.filter(status=status_obj)

            # add priority filter here


            response = []
            for task in tasks:
                print(task.due_date.date() == datetime.date.today())
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

    def post(self, request):
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


        label_obj = Label.objects.get(name=label)

        status_obj = Status.objects.get(status=task_status)

        task_obj = Task.objects.create(name=name, description=description, due_date=due_date,
                                        list_obj=list_obj, label=label_obj, status=status_obj
                                        )


        return Response("Task created successfully", status=status.HTTP_201_CREATED)

    def put(self, request):
        task_id = request.data["id"]
        task_obj = Task.objects.get(pk=task_id)
        if "name" in request.data:
            task_obj.name = request.data["name"]
        if "description" in request.data:
            task_obj.description = request.data["description"]

        if "label" in request.data:
            task_obj.label = Label.objects.get(name=request.data["label"])

        if "status" in request.data:
            task_obj.status = Status.objects.get(status=request.data["status"])

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


    def delete(self, request):
        task_id = int(request.data["id"])
        print(task_id)
        t = Task.objects.get(pk=task_id)
        t.delete()

        return JsonResponse("Deleted successfully", safe=False)



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
        print(email, subscribe)
        if subscribe:
            try:
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

@background(schedule=datetime.datetime(2020, 5, 30, 8, 0))
def test_email():
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


def background_test(request):
    test_email(repeat=43200, repeat_until=datetime.datetime(2020, 7, 31, 8, 0))
    return JsonResponse("Done", safe=False)
