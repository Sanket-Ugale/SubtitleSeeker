from django.urls import path
from subtitlesApp import views

urlpatterns = [
    # path('process_video/', views.process_video, name='process_video'),
    # Add other URL patterns as needed
    path('login/', views.login),
    path('', views.home, name='home'),
]