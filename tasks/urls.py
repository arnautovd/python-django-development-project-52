from django.urls import path

from .views import home

app_name = 'tasks'

urlpatterns = [
    path('', home, name='home'),
]
