# backend/products/models.py
import random
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    code = models.CharField(max_length=10, unique=True, editable=False, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            new_code = None
            while True:
                new_code = str(random.randint(100000, 999999))
                if not Product.objects.filter(code=new_code).exists():
                    break
            self.code = new_code
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
