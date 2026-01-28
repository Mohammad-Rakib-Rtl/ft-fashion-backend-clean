# backend/products/models.py
import random
from django.db import models
from cloudinary.models import CloudinaryField

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(blank=True,  null=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = CloudinaryField('image')
    code = models.CharField(max_length=10, unique=True, editable=False, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    #fixing my latest bug
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
        return self.code
    
    def get_image_url(self):
        """Return the full Cloudinary URL for the image"""
        if self.image:
            # Get the actual URL
            url = self.image.url
            
            # If it's a local path, construct the Cloudinary URL
            if url.startswith('/media/'):
                cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
                if cloud_name:
                    filename = url.replace('/media/', '')
                    return f"https://res.cloudinary.com/{cloud_name}/image/upload/{filename}"
            
            return url
        
        return ""

    def __str__(self):
        return self.code
