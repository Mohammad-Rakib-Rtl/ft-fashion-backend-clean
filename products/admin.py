# backend/products/admin.py
from django.contrib import admin
from .models import Product, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']
    ordering = ['-id']  # Order by ID descending (newest first)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['get_product_name', 'category', 'price', 'code', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['code', 'created_at']
    ordering = ['-created_at']  # Order by creation date descending (newest first)
    
    def get_product_name(self, obj):
        return obj.name or f"Product {obj.id}"
    get_product_name.short_description = 'Name'  # Column header
    
    # Custom form to handle optional name field
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'name':
            kwargs['required'] = False  # Make name field optional in admin
        return super().formfield_for_dbfield(db_field, **kwargs)