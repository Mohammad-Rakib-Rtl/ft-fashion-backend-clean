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
        
        # Replace category ID with category name
        if instance.category:
            representation['category'] = instance.category.name
        
        return representation    