from django.urls import path
from home.views import *
from django.contrib import admin

urlpatterns = [
    path('', home_view, name='home'),
    path('home/', home_view, name='home'),
    path('home/trip/<int:pk>/', home_trip_details, name='home_trip_details'),
]
