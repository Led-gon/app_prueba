from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import os
from django.conf import settings


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('Empleado', 'Empleado'),
        ('Administrador', 'Administrador'),
        ('Super Usuario', 'Super Usuario'),
        ('cocinero', 'Cocinero'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Empleado')

    # Add related_name to avoid clashes with default User model if you were using it directly
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="customuser_groups", # Changed related_name
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_permissions", # Changed related_name
        related_query_name="customuser",
    )

    def __str__(self):
        return self.username

class Product(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly define primary key
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=220, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    idCategoria = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products', blank=True, null=True)
    idPromotion = models.ForeignKey('Promotion', on_delete=models.CASCADE, related_name='products', blank=True, null=True)
    active = models.BooleanField(default=True)  # To mark if the product is active or not

    def save(self, *args, **kwargs):
        if self.image:
            image_path = os.path.join(settings.MEDIA_ROOT, os.path.basename(self.image.name))
            if os.path.exists(image_path):
                # Si la imagen ya existe, usa la existente
                self.image.name = f'{os.path.basename(self.image.name)}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Category(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly define primary key
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Promotion(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly define primary key
    description = models.TextField(max_length=220, blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name

class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly define primary key
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_orders')
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_items')
    sugerency = models.TextField(max_length=220, blank=True, null=True)  # Optional field for suggestions
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Calculated as quantity * price
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Price at the time of order

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"

    def save(self, *args, **kwargs):
        # If the product is not set, raise an error
        if not self.product:
            raise ValueError("Product must be set for OrderItem.")
        # If the product's price is not set, use the product's current price
        if not self.price:
            if self.product.stock <= 0:
                raise ValueError("Cannot add product to order item because it is out of stock.")
            if self.product.active is False:
                raise ValueError("Cannot add product to order item because it is not active.")
            self.price = self.product.price
        # Calculate subtotal
        self.subtotal = self.quantity * self.price
        super().save(*args, **kwargs)

    

class State(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly define primary key
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly define primary key
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Total amount of the order
    status = models.ForeignKey(State, on_delete=models.CASCADE, related_name='status', default=1)  # Default to first state
    IP = models.GenericIPAddressField(blank=True, null=True)  # Optional field for IP address
    initialTime = models.DateTimeField(default=timezone.now, blank=True)  # Timestamp when the order was created
    endTime = models.DateTimeField(auto_now=True)  # Timestamp when the order was last updated
    order_date = models.DateField(default=timezone.now) # Use timezone.now for default
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    tableNumber = models.DecimalField(max_digits=5, decimal_places=0, blank=False, null=False) 

    def __str__(self):
        return f"Order {self.id} - {self.status.name} - {self.order_date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def update_amount(self):
        total = sum(item.subtotal for item in self.order_items.all())
        self.amount = total
        self.save(update_fields=['amount'])




class PaymentMethod(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly define primary key
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class PaymentStatus(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly define primary key
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class Payment(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly define primary key
    idOrder = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    idPaymentMethod = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    idPaymentStatus = models.ForeignKey(PaymentStatus, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateTimeField(auto_now_add=True)
    motive = models.TextField(max_length=220, blank=True, null=True)  # Optional field for payment motive
    token = models.CharField(max_length=255, blank=False, null=False, default="aaaaxx3322-55sdf4")  # Optional field for payment token

    def __str__(self):
        return f"Payment {self.id} for Order {self.idOrder.id} - {self.idPaymentMethod.name} - {self.amount}"



