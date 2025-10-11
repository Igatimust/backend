from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string
from django.contrib.auth.models import User

# User model- will store the users of igati
class Users(models.Model):
    # firebase_uid = models.CharField(max_length=128, unique=True)  # UID from Firebase
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    password = models.CharField(max_length=128, default= "weeeeeeeee")
    email = models.EmailField(unique=True)
    phoneNumber = models.CharField(max_length=15, unique=True)

    ROLES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    role = models.CharField(max_length=100, choices=ROLES, default='user')

    def __str__(self):
        return f"{self.firstName} {self.lastName} ({self.email})"



# Project model- will store the igati projects
class Project(models.Model):
    owner = models.ForeignKey(Users, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.URLField(blank=True, null=True, default='https://res.cloudinary.com/dc68huvjj/image/upload/v1748119193/zzy3zwrius3kjrzp4ifc.png')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.owner.email} on {self.created_at}"

# melby model for paystack payments
class PaymentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('expired', 'Expired'),
        ('failed', 'Failed'),
    ]
    
    reference_no = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    user_id = models.CharField(max_length=50, default='guest')
    email = models.EmailField(max_length=255, default='customer@email.com')
    phone = models.CharField(max_length=20, blank=True, null=True, default='')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_channel = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    authorization_url = models.URLField(max_length=500, blank=True, null=True)
    access_code = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=10, default='KES')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    paid_at = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.reference_no:
            self.reference_no = self.generate_unique_reference()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def generate_unique_reference(self):
        while True:
            reference = ''.join(random.choices(string.digits, k=10))
            if not PaymentRequest.objects.filter(reference_no=reference).exists():
                return reference
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Payment {self.reference_no} - KES {self.amount}"

# end of PaymentRequest model

# Cart model- will store the shopping cart for users - caroline
# cart/models.py

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Honey', 'Honey'),
        ('Maize', 'Maize'),
        ('Maize flour', 'Maize flour'),
        ('Hen', 'Hen'),
    ]
    seller = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="products", default=1)
    name = models.CharField(max_length=100)
    description = models.TextField(default="Product description")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="Honey")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.URLField(blank=True, null=True, default='https://res.cloudinary.com/dc68huvjj/image/upload/v1748119193/zzy3zwrius3kjrzp4ifc.png')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} (Ksh{self.price}) {self.stock}"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return sum(item.total() for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total(self):
        return self.product.price * self.quantity

# end of Cart model

# productOrder model - ushindi
class ProductOrder(models.Model):
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='products')
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_orders', default=1)
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.userId.name} for {self.product_name}"


# user notification mdoel - ushindi
class Notification(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', default=1)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification {self.id} for {self.userId.name}"