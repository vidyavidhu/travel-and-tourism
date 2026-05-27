from django.urls import path
from . import views

urlpatterns = [
    path('initiate/<int:booking_id>/', views.initiate_payment, name='initiate_payment'),
    path('process/<int:payment_id>/', views.process_payment, name='process_payment'),
    path('success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('failed/<int:payment_id>/', views.payment_failed, name='payment_failed'),
    path('history/', views.payment_history, name='payment_history'),
    path('invoice/<int:payment_id>/', views.download_invoice, name='download_invoice'),
]
