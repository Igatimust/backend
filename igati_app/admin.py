from django.contrib import admin
from .models import User, Product, Project, PaymentRequest, Cart, CartItem

# Register your models here.
admin.site.register(User)
admin.site.register(Product)
admin.site.register(Project)
admin.site.register(PaymentRequest)
admin.site.register(Cart)
admin.site.register(CartItem)
