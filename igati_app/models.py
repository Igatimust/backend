from django.db import models
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string

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


# Product model- will store the products listed by users/igati
class Product(models.Model):
    seller = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (Ksh{self.price}) {self.stock}"


# Project model- will store the igati projects
class Project(models.Model):
    owner = models.ForeignKey(Users, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.owner.email} on {self.created_at}"


# Order model- will store the orders placed by users
class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    buyer = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.buyer.email}"


# OrderItem model- will store the items in an order
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot price

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"


# Payment model- will store the payment details for orders
class Payment(models.Model):
    METHOD_CHOICES = [
        ("mpesa", "M-Pesa"),
        ("card", "Card"),
        ("paypal", "PayPal"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("successful", "Successful"),
        ("failed", "Failed"),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment for Order {self.order.id} - {self.status}"

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