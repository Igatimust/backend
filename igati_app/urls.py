from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # celestine - urls
    # User Authentication APIs
    path('register/', views.register, name='register'),
    path('login/<str:email>/<str:password>/', views.login, name='login'),

    # melby -urls
    # Main Payment APIs
    path('initialize/', views.initialize_payment, name='initialize_payment'),
    path('callback/', views.payment_callback, name='payment_callback'),
    path('status/<str:reference_no>/', views.check_payment_status, name='check_payment_status'),
    path('list/', views.list_payments, name='list_payments'),

    # caroline - urls
    # Shopping Cart APIs
    path('product_list/', views.product_list, name='product_list'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('increase/<int:product_id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('cart/', views.cart_view, name='cart_view'),

    # ushindi -urls
    # projects apis
    path('projects/', views.get_projects, name='get_projects'),
    path('projects/add/', views.add_project, name='add_project'),

    # product order apis
    path('add_product/', views.add_product, name='add_product'),
    path('create_bulk_order/', views.create_bulk_order, name='create_bulk_order'),

    # notifications api
    path('get_user_notifications/<int:user_id>/', views.get_user_notifications, name='get_user_notifications'),
]
