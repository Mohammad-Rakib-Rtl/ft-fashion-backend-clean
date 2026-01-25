from rest_framework import serializers
from .models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'




class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'category', 'category_name', 'name', 'description', 'price', 'image', 'code', 'created_at']
        read_only_fields = ['id', 'created_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Ensure we return the full Cloudinary URL for the image
        if instance.image:
            # Get the actual URL
            url = instance.image.url
            
            # If it's a local path, construct the Cloudinary URL
            if url.startswith('/media/'):
                # Try to get cloud name from environment
                from django.conf import settings
                cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', 'di5e3wbjt')
                filename = url.replace('/media/', '')
                url = f"https://res.cloudinary.com/{cloud_name}/image/upload/{filename}"
            
            representation['image'] = url
        
        # Replace category ID with category name
        if instance.category:
            representation['category'] = instance.category.name
        
        return representation
    
 