from django.contrib import admin
from .models import Users, Product, Project, Order, OrderItem, Payment, PaymentRequest

# Register your models here.
admin.site.register(Users)
admin.site.register(Product)
admin.site.register(Project)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(PaymentRequest)
