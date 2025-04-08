from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Wishlist, WishlistItem
from products.models import ProductWithImages
from cart.models import Cart, CartItem
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


"""
WISHLIST PAGE
"""
@login_required
def wishlist_view(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist_items = wishlist.items.all()

    page = request.GET.get('page', 1)
    paginator = Paginator(wishlist_items, 10)

    try:
        wishlist_items = paginator.page(page)
    except PageNotAnInteger:
        wishlist_items = paginator.page(1)
    except EmptyPage:
        wishlist_items = paginator.page(paginator.num_pages)

    context = {
        'wishlist_items': wishlist_items,
        'wishlist_count': wishlist_items.paginator.count,
    }
    return render(request, 'user/wishlist.html', context)


"""
ADD TO WISHLIST
"""
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(ProductWithImages, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    # Check if the product is already in the wishlist
    if WishlistItem.objects.filter(wishlist=wishlist, product=product).exists():
        messages.error(request, 'Product is already in your wishlist.')
    else:
        WishlistItem.objects.create(wishlist=wishlist, product=product)
        messages.success(request, 'Product added to wishlist.')

    return redirect(request.META.get('HTTP_REFERER', 'wishlist'))


"""
REMOVE FROM WISHLIST
"""
@login_required
def remove_from_wishlist(request, item_id):
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist__user=request.user)
    wishlist_item.delete()
    messages.success(request, 'Product removed from wishlist.')
    return redirect('wishlist')



"""
MOVE TO CART
"""
@login_required
def move_to_cart(request, item_id):
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist__user=request.user)
    product = wishlist_item.product

    # Check if the product is already in the cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    if CartItem.objects.filter(cart=cart, product_variant__product=product).exists():
        messages.error(request, 'Product is already in your cart.')
    else:
        # Assuming the product has a default variant
        product_variant = product.variants.first()
        if not product_variant:
            messages.error(request, 'No valid variant found for this product.')
        else:
            CartItem.objects.create(cart=cart, product_variant=product_variant, quantity=1)
            wishlist_item.delete()
            messages.success(request, 'Product moved to cart.')

    return redirect('wishlist')