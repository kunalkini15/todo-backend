from django.urls import path
from todo_app import views

urlpatterns = [
    path('register/', views.Register.as_view(), name="register"),
    path('login/', views.Login.as_view(), name="login"),
    path('user/', views.UserView.as_view(), name="user"),
    path('lists/', views.ListView.as_view(), name="lists"),
    path('tasks/', views.TaskView.as_view(), name="tasks"),
    path('tasks/<int:task_id>/', views.TaskView.as_view(), name="single_task"),
    path('test_email/', views.test_email, name="test_email"),
    path('subscribe/', views.SubscriptionView.as_view(), name="subscribe"),
    path('test_background/', views.background_test, name="background_test"),
    path('test_report/', views.PerformanceView.as_view(), name="test_report"),
    path("report_email/", views.email_report, name="report_email")
]
