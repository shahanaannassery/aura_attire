from django.urls import path
from . import views


urlpatterns = [
    #Product Management
    path("management", views.product_list, name='product_management'),

    # Create Product
    path("create", views.create_product, name='create_product'),

    # # Edit Product
    path("edit/<int:product_id>", views.edit_product, name='edit_product'),

    # Toggle Product Listing (for admin)
    path('list/<int:product_id>/', views.toggle_product_listing, name='list_unlist'),

    # # Product Details View
    path('<int:product_id>/', views.product_details, name='product_details'),

     # Category Products
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    path('check_stock/', views.check_stock, name='check_stock'),

    # path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),




    # # Variant Management
    path('variant/<int:product_id>/', views.variant_list, name='variant'),
    path('variant/add/<int:product_id>/', views.add_variant, name='add_variant'),  # Add variant (color, size, stock)
    path('variant/update/<int:variant_id>', views.update_variant, name='update_variant'),  # Update variant (color, size, stock)
    path('variant/delete/<int:variant_id>', views.delete_variant, name='delete_variant'),  # Delete variant
    


]