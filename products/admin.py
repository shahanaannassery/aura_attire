# from django.contrib import admin

# # Register your models here.
# from . models import ProductWithImages

# admin.site.register(ProductWithImages)

# products/admin.py
from django.contrib import admin
from .models import ProductWithImages, ProductVariant

class ProductWithImagesAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_listed', 'created_at']
    list_filter = ['category', 'is_listed']
    search_fields = ['name']

admin.site.register(ProductWithImages, ProductWithImagesAdmin)
