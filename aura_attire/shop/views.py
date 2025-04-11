from django.shortcuts import render, HttpResponse
from products.models import ProductWithImages
from category.models import Category
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

###############################################USER SIDE###############################################
"""
SHOP OR ALL PRODUCT LISTING PAGE
"""

def all_products(request):
    products = ProductWithImages.objects.filter(is_listed=True,category__is_listed = True)  # Fetch listed products
    categories = Category.objects.filter(is_listed=True,)

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(name__icontains=search_query)

    # Filtering
    selected_categories = request.GET.getlist('categories')  # Retrieve selected category IDs
    if selected_categories:
        products = products.filter(category__id__in=selected_categories)

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
    else:
        products = products.order_by('id')  # Default ordering for stability

    # Pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = {
        'products': [{
            'product': product,
            'first_image': product.image1  # Get the first image directly
        } for product in products],
        'categories': categories,
        'selected_categories': [int(cat) for cat in selected_categories],
        'search_query': search_query,
        'sort_option': sort_option,
        'page_obj': products,  # Pagination object
    }

    return render(request, 'user/all_products.html', context)

###############################################USER SIDE###############################################