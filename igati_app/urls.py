from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/<str:email>/<str:password>/', views.login, name='login')
    # melby -urls
    # Main Payment APIs
    path('initialize/', views.initialize_payment, name='initialize_payment'),
    path('callback/', views.payment_callback, name='payment_callback'),
    path('status/<str:reference_no>/', views.check_payment_status, name='check_payment_status'),
    path('list/', views.list_payments, name='list_payments'),
]
