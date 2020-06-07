from django.urls import path
from todo_app import views

urlpatterns = [
    path('register/', views.Register.as_view(), name="register"),
    path('login/', views.Login.as_view(), name="login"),
    path('user/', views.UserView.as_view(), name="user"),
    path('lists/', views.ListView.as_view(), name="lists"),
    path('tasks/', views.TaskView.as_view(), name="tasks"),
    path('subscribe/', views.SubscriptionView.as_view(), name="subscribe"),
    path('get_progress_report/', views.PerformanceView.as_view(), name="get_progress_report"),
    path('single_task/', views.get_single_task, name="single_task"),
    path('start_email_service/', views.call_background_email_service, name="start_email_service"),
    path("send_report_via_email/", views.send_report_via_email, name="report_email")
]
