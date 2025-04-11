from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ProductWithImages,ProductVariant
from category.models import Category
from decimal import Decimal, InvalidOperation
from admin_side.views import is_admin
from django.contrib.auth.decorators import user_passes_test
from django.core.files.base import ContentFile
from django.db.models import Q
import json
import random
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import cloudinary.uploader
from django.http import Http404
from reviews.models import Review


"""
PRODUCT LISTING
"""
@user_passes_test(is_admin)
def product_list(request):
    query = request.GET.get('q', '')
    products = ProductWithImages.objects.all()

    if query:
        products = products.filter(name__icontains=query)

    # Sort products to show the last added products first
    products = products.order_by('-id')

    page = request.GET.get('page', 1)
    paginator = Paginator(products, 8)

    try:
        paginated_products = paginator.page(page)
    except PageNotAnInteger:
        paginated_products = paginator.page(1)
    except EmptyPage:
        paginated_products = paginator.page(paginator.num_pages)

    # Recalculate final_offer_price for the paginated products
    # for product in paginated_products:
    #     product.final_offer_price = product.best_offer_price

    categories = Category.objects.all()
    return render(request, 'admin/product_list.html', {
        'products': paginated_products,
        'categories': categories,
        'query': query,
    })


"""
CREATE PRODUCT
"""
def create_product(request):
    if request.method == "POST":
        form_data = {
            'name': request.POST.get('name', ''),
            'description': request.POST.get('description', ''),
            'category': request.POST.get('category', ''),
            'price': request.POST.get('price', ''),
        }

        errors = []
        try:
            # Validation
            name = form_data['name']
            description = form_data['description']
            category_id = form_data['category']

            # Validate price
            try:
                price = Decimal(form_data['price'])
                if price <= 0:
                    errors.append("Price must be greater than zero.")
            except (InvalidOperation, ValueError):
                errors.append("Price must be a valid decimal number.")

            if not name:
                errors.append("Product name is required.")
            if not description:
                errors.append("Description is required.")
            if not category_id:
                errors.append("Category is required.")
            else:
                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    errors.append("Selected category does not exist.")

            # Get images
            image1 = request.FILES.get('image1')  # Single image
            image2 = request.FILES.get('image2')  # Second image
            image3 = request.FILES.get('image3')  # Third image

            # Validate images
            if not image1 and not image2 and not image3:
                errors.append("Please upload at least one image.")

            if errors:
                raise ValueError("Validation Error")

            # Create the product
            product = ProductWithImages.objects.create(
                name=name,
                description=description,
                category=category,
                price=price,
            )

            # Process and upload images to Cloudinary
            if image1:
                try:
                    cloudinary_response = cloudinary.uploader.upload(image1)
                    product.image1 = cloudinary_response['secure_url']
                except Exception as img_error:
                    errors.append(f"Image 1 processing error: {str(img_error)}")

            if image2:
                try:
                    cloudinary_response = cloudinary.uploader.upload(image2)
                    product.image2 = cloudinary_response['secure_url']
                except Exception as img_error:
                    errors.append(f"Image 2 processing error: {str(img_error)}")

            if image3:
                try:
                    cloudinary_response = cloudinary.uploader.upload(image3)
                    product.image3 = cloudinary_response['secure_url']
                except Exception as img_error:
                    errors.append(f"Image 3 processing error: {str(img_error)}")

            # Save the product with images
            if not errors:
                product.save()

            if errors:
                raise ValueError("Some images could not be processed.")

            messages.success(request, "Product created successfully!")
            return redirect('product_management')

        except Exception as e:
            messages.error(request, "Error creating product. Please check the form and try again.")
            categories = Category.objects.filter(is_listed=True)
            return render(request, 'admin/add_product.html', {
                'categories': categories,
                'form_data': form_data,
                'errors': errors,
            })

    categories = Category.objects.filter(is_listed=True)
    return render(request, 'admin/add_product.html', {'categories': categories})


"""
EDIT PRODUCT
"""
@user_passes_test(is_admin)
def edit_product(request, product_id):
    product = get_object_or_404(ProductWithImages, pk=product_id)

    if request.method == 'POST':
        category_id = request.POST.get('category')
        category = get_object_or_404(Category, pk=category_id)  

        product_name = request.POST.get('product_name')
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price')
        description = request.POST.get('description')
        quantity = request.POST.get('quantity')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        image3 = request.FILES.get('image3')

        errors = []

        if not image1 and not image2 and not image3 and not (product.image1 or product.image2 or product.image3):
            errors.append("Please upload at least one image.")

        if not errors:
            product.category = category  
            product.name = product_name  
            product.price = price
            product.discount_price = discount_price
            product.description = description
            product.quantity = quantity

            if image1:
                cloudinary_response = cloudinary.uploader.upload(image1)
                product.image1 = cloudinary_response['secure_url']
            if image2:
                cloudinary_response = cloudinary.uploader.upload(image2)
                product.image2 = cloudinary_response['secure_url']
            if image3:
                cloudinary_response = cloudinary.uploader.upload(image3)
                product.image3 = cloudinary_response['secure_url']

            product.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('product_management')

    categories = Category.objects.filter(is_listed=True)
    return render(request, 'admin/edit_product.html', {'product': product, 'categories': categories})


'''
delete product
'''

# def delete_product(request, product_id):
#     # Use get_object_or_404 to automatically raise a 404 error if the product doesn't exist
#     product = get_object_or_404(ProductWithImages, id=product_id)

#     # Delete the product if it exists
#     product.delete()

#     # Redirect back to the previous page (product list page)
#     return redirect(request.META.get('HTTP_REFERER', 'products/list/'))

"""
LISTING AND UNLISTING THE PRODUCTS
"""
@user_passes_test(is_admin)
def toggle_product_listing(request, product_id):
    try:
        product = ProductWithImages.objects.get(id=product_id)
        product.is_listed = not product.is_listed
        product.save()
        status = "listed" if product.is_listed else "unlisted"
        messages.success(request, f"Product successfully {status}")
    except ProductWithImages.DoesNotExist:
        messages.error(request, "Product not found")
    return redirect('product_management')


# """
# PRODUCT DETAILS PAGE
# """
# def product_details(request, product_id):
#     product = get_object_or_404(ProductWithImages, id=product_id)
    
#     # # Get all variants that are in stock
#     # variants = product.variants.filter(stock__gt=0)
    
#     # # Get unique colors and sizes
#     # unique_colors = variants.values_list('color', flat=True).distinct()
    
#     # # Create a dictionary with colors as keys and their available sizes as values
#     # color_size_dict = {}
#     # for color in unique_colors:
#     #     color_size_dict[color] = list(variants.filter(color=color).values_list('size', flat=True).distinct())

#      # Fetch all images from the product
#     product_images = [product.image1, product.image2, product.image3]
#     product_images = [img for img in product_images if img]  # Remove None values
    
#     # Get related products (optional)
#     related_products = ProductWithImages.objects.filter(category=product.category).exclude(id=product_id)
#     related_products = random.sample(list(related_products), min(len(related_products), 5))
    
#     # if request.user.is_authenticated:
#     #     can_review = Review.can_review(request.user, product)

#     context = {
#         'product': product,
#         # 'unique_colors': unique_colors,
#         # 'color_size_dict': json.dumps(color_size_dict),  # Convert to JSON string
#         'product_images': product_images,
#         'related_products': related_products,
#         # 'can_review': can_review,
#     }
#     return render(request, 'user/product_details.html', context)


# products/views.py


def product_details(request, product_id):
    # Get the product or return a 404 error if not found
    product = get_object_or_404(ProductWithImages, id=product_id)

     # Get all variants that are in stock
    variants = product.variants.filter(stock__gt=0)

    # Get unique colors and sizes
    unique_colors = variants.values_list('color', flat=True).distinct()

    # Create a dictionary with colors as keys and their available sizes as values
    color_size_dict = {}
    for color in unique_colors:
        color_size_dict[color] = list(variants.filter(color=color).values_list('size', flat=True).distinct())
    


    # Fetch all images from the product
    product_images = [product.image1, product.image2, product.image3]
    product_images = [img for img in product_images if img]  # Remove None values
    
    # Get related products (optional)
    related_products = ProductWithImages.objects.filter(category=product.category).exclude(id=product_id)
    related_products = random.sample(list(related_products), min(len(related_products), 5))

    can_review = Review.can_review(request.user, product)
    
    context = {
        'product': product,
        'product_images': product_images,
        'related_products': related_products,
        'unique_colors': unique_colors,
        'color_size_dict': json.dumps(color_size_dict),  # Convert to JSON string
        'can_review': can_review,
    }
    return render(request, 'user/product_details.html', context)


"""
CATEGORY BASED PRODUCT LISTING
"""
def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id, is_listed=True)
    products = ProductWithImages.objects.filter(category=category, is_listed=True).prefetch_related('variants')

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(name__icontains=search_query)

    # Sorting
    sort_option = request.GET.get('sort', '')  
    if sort_option == 'name-asc':
        products = products.order_by('name')  
    elif sort_option == 'name-desc':
        products = products.order_by('-name') 
    elif sort_option == 'price-asc': 
        products = products.order_by('price')
    elif sort_option == 'price-desc': 
        products = products.order_by('-price')

    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = {
        'category': category,
        'products': [{
            'product': product,
            'first_image': product.image1
        } for product in products],
        'search_query': search_query,
        'sort_option': sort_option,
        'page_obj': products,
    }
    return render(request, 'user/category_products.html', context)




"""
ADD VARIANT
"""
@user_passes_test(is_admin)
def add_variant(request, product_id):
    product = get_object_or_404(ProductWithImages, id=product_id)

    if request.method == "POST":
        color = request.POST.get('color', '').strip()
        size = request.POST.get('size', '').strip()
        stock = request.POST.get('stock', '').strip()

        errors = []

        # Validation checks
        if not color:
            errors.append("Color is required.")
        if not size:
            errors.append("Size is required.")
        try:
            stock = int(stock)
            if stock < 0:
                errors.append("Stock cannot be negative.")
        except ValueError:
            errors.append("Stock must be a valid number.")

        # Check for duplicates (same color and size for the product) - case insensitive
        if ProductVariant.objects.filter(product=product).filter(
            color__iexact=color, size__iexact=size).exists():
            errors.append("This variant already exists.")

        if errors:
            # If there are errors, render the form with error messages
            for error in errors:
                messages.error(request, error)
            return render(request, 'admin/add_variant.html', {'product': product, 'errors': errors, 'color': color, 'size': size, 'stock': stock})

        try:
            # Create the variant
            ProductVariant.objects.create(product=product, color=color, size=size, stock=stock)
            messages.success(request, "Variant added successfully!")
            return redirect('variant', product_id=product_id)
        except Exception as e:
            messages.error(request, f"Error adding variant: {str(e)}")
            return render(request, 'admin/add_variant.html', {'product': product})

    return render(request, 'admin/add_variant.html', {'product': product})



"""
VARIANT LISTING
"""
@user_passes_test(is_admin)
def variant_list(request, product_id):
    product = get_object_or_404(ProductWithImages, id=product_id)
    variants = product.variants.all()  

    page = request.GET.get('page', 1)  
    paginator = Paginator(variants, 10)  
    try:
        variants = paginator.page(page)
    except PageNotAnInteger:
        variants = paginator.page(1)
    except EmptyPage:
        variants = paginator.page(paginator.num_pages)

    return render(request, 'admin/variant.html', {'product': product, 'variants': variants})


"""
UPDATE VARIANT
"""
@user_passes_test(is_admin)
def update_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)

    if request.method == "POST":
        color = request.POST.get('color', '').strip()
        size = request.POST.get('size', '').strip()
        stock = request.POST.get('stock', '').strip()

        # List to store error messages
        errors = []

        # Validation checks
        if not color or not size:
            errors.append("Color and Size are required.")
        
        if stock.isdigit() and int(stock) < 0:
            errors.append("Stock cannot be negative.")

        # Check for duplicate combination (if another variant with same color & size exists) - case insensitive
        if ProductVariant.objects.filter(product=variant.product).filter(
            color__iexact=color, size__iexact=size).exclude(id=variant.id).exists():
            errors.append("This variant already exists.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'admin/edit_variant.html', {'variant': variant, 'errors': errors})

        try:
            # Update the variant if no errors
            variant.color = color
            variant.size = size
            variant.stock = int(stock)
            variant.save()

            messages.success(request, "Variant updated successfully!")
            return redirect('variant', product_id=variant.product.id)

        except Exception as e:
            messages.error(request, f"Error updating variant: {str(e)}")
            return render(request, 'admin/edit_variant.html', {'variant': variant})

    return render(request, 'admin/edit_variant.html', {'variant': variant})


"""
DELETE VARIANT
"""
@user_passes_test(is_admin)
def delete_variant(request, variant_id):
    # Get the variant object or 404 if not found
    variant = get_object_or_404(ProductVariant, id=variant_id)
    variant.delete()
    return redirect('variant', product_id=variant.product.id)




"""
STOCK CHECKING WHEN ADDING TO CART/CHECKOUT
"""
def check_stock(request):
    if request.method == "POST":
        color = request.POST.get('color')
        size = request.POST.get('size')
        variants = ProductVariant.objects.filter(product__is_listed=True)
        variant_data = [{'color': variant.color, 'size': variant.size, 'stock': variant.stock} for variant in variants]
        return JsonResponse({'variants': variant_data})
    return JsonResponse({'error': 'Invalid request'}, status=400)