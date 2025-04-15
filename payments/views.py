
from decimal import Decimal
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, JsonResponse
from orders.models import Order, OrderItem
from cart.models import Cart, CartItem
from products.models import ProductVariant
from couponsapp.models import Coupon, CouponUsage
from wallet.models import Wallet
from user_profile.models import Address, ShippingAddress
import logging
from django.contrib import messages
from django.shortcuts import redirect, reverse
from offers.models import ProductOffer, CategoryOffer

# log set for debug
logger = logging.getLogger(__name__)

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))

"""
PAYMENT INITIALISATION OF RAZORPAY
"""
@csrf_exempt
def initiate_payment(request):
    if request.method == "POST":
        user = request.user
        address_id = request.POST.get("address_id")
        payment_method = request.POST.get("payment_method")

        addresses = Address.objects.filter(user=user, is_deleted=False)
        default_address = addresses.filter(is_default=True).first()

        if not address_id or not payment_method:
            return JsonResponse({"error": "Address or payment method not provided."}, status=400)

        try:
            # Handle address selection
            if address_id == "new":
                shipping_address = ShippingAddress.objects.create(
                    user=user,
                    name=request.POST.get('name'),
                    address=request.POST.get('address'),
                    city=request.POST.get('city'),
                    state=request.POST.get('state'),
                    country=request.POST.get('country'),
                    postcode=request.POST.get('postcode'),
                    phone=request.POST.get('phone'),
                )
            elif address_id:
                address = Address.objects.get(id=address_id, user=user)
                shipping_address = ShippingAddress.objects.create(
                    user=user,
                    name=address.name,
                    address=address.address,
                    city=address.city,
                    state=address.state,
                    country=address.country,
                    postcode=address.postcode,
                    phone=address.phone,
                )
            else:
                if not default_address:
                    return JsonResponse({"error": "No valid address found."}, status=400)
                shipping_address = ShippingAddress.objects.create(
                    user=user,
                    name=default_address.name,
                    address=default_address.address,
                    city=default_address.city,
                    state=default_address.state,
                    country=default_address.country,
                    postcode=default_address.postcode,
                    phone=default_address.phone,
                )

            # Fetch cart and calculate totals
            cart = Cart.objects.get(user=user)
            cart_items = CartItem.objects.filter(cart=cart)

            if not cart_items.exists():
                return JsonResponse({"error": "Your cart is empty. Please add items to checkout."}, status=400)

            total_offer_price = Decimal('0.00')
            for item in cart_items:
                if item.quantity > item.product_variant.stock:
                    return JsonResponse({"error": f"Not enough stock for {item.product_variant.product.name}."}, status=400)
                
                product = item.product_variant.product
                product_offer = ProductOffer.objects.filter(product=product, is_active=True).first()
                category_offer = CategoryOffer.objects.filter(category=product.category, is_active=True).first()

                # Calculate the final price based on the best offer
                if product_offer and category_offer:
                    final_price = min(
                        product.price * (1 - product_offer.discount_percentage / 100),
                        product.price * (1 - category_offer.discount_percentage / 100)
                    )
                elif product_offer:
                    final_price = product.price * (1 - product_offer.discount_percentage / 100)
                elif category_offer:
                    final_price = product.price * (1 - category_offer.discount_percentage / 100)
                else:
                    final_price = product.price

                quantity = Decimal(str(item.quantity))
                total_offer_price += final_price * quantity

            delivery_charge = Decimal('40.00') if total_offer_price < Decimal('1000.00') else Decimal('0.00')
            grand_total = total_offer_price + delivery_charge

            # Apply coupon discount if any
            coupon_discount = Decimal('0.00')
            coupon_code = request.session.get('coupon_code', None)
            coupon = None
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(coupon_code=coupon_code, is_active=True)
                    if coupon.is_valid() and total_offer_price >= coupon.minimum_purchase_amount:
                        if not CouponUsage.objects.filter(user=user, coupon=coupon).exists():
                            coupon_discount = (coupon.discount_percentage / Decimal('100.00')) * total_offer_price
                            if coupon_discount > coupon.max_discount_amount:
                                grand_total -= coupon.max_discount_amount
                                coupon_discount = coupon.max_discount_amount
                            else:
                                grand_total -= coupon_discount
                            
                except Coupon.DoesNotExist:
                    pass

            # Create the order first
            order = Order.objects.create(
                user=user,
                shipping_address=shipping_address,
                payment_method=payment_method,
                total_price=grand_total,
                payment_status='Processing',
                status='processing',
                coupon=coupon if coupon_code else None,
                discount_coupon_amount = coupon_discount,
                balance_refund = coupon_discount,
            )

            # Store order items and update stock
            for item in cart_items:
                product_variant = item.product_variant
                product = product_variant.product
                product_offer = ProductOffer.objects.filter(product=product, is_active=True).first()
                category_offer = CategoryOffer.objects.filter(category=product.category, is_active=True).first()

                # Calculate the final price based on the best offer
                if product_offer and category_offer:
                    final_price = min(
                        product.price * (1 - product_offer.discount_percentage / 100),
                        product.price * (1 - category_offer.discount_percentage / 100)
                    )
                elif product_offer:
                    final_price = product.price * (1 - product_offer.discount_percentage / 100)
                elif category_offer:
                    final_price = product.price * (1 - category_offer.discount_percentage / 100)
                else:
                    final_price = product.price

                # Create a separate OrderItem for each quantity
                for _ in range(item.quantity):
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_variant=product_variant,
                        quantity=1, 
                        price=final_price,
                    )
                    product_variant.stock -= 1
                    product_variant.save()
                        
            # Record coupon usage
            if coupon_code:
                CouponUsage.objects.create(user=user, coupon=coupon)
                del request.session['coupon_code']

            # Store cart details in session
            request.session['cart_details'] = {
                'order_id': order.id,
                'shipping_address_id': shipping_address.id,
                'payment_method': payment_method,
                'total_price': str(grand_total),
                'cart_items': [{'product_variant_id': item.product_variant.id, 'quantity': item.quantity} for item in cart_items],
                'coupon_code': coupon_code,
                'coupon_discount': str(coupon_discount),
            }

            # Handle payment methods
            if payment_method == "COD" or payment_method == "wallet":
                if payment_method == "wallet":
                    wallet = Wallet.objects.get(user=user)
                    if wallet.balance < grand_total:
                        return JsonResponse({"error": "Insufficient funds in wallet."}, status=400)
                return create_order(request)
            elif payment_method == "razorpay":
                amount = int(grand_total * 100)  # Convert to paise
                razorpay_order = razorpay_client.order.create({
                    "amount": amount,
                    "currency": "INR",
                    "receipt": f"order_{order.id}",
                    "notes": {
                        "django_order_id": order.id,
                        "user_id": user.id,
                    },
                })
                callback_url = reverse('order_success', args=[order.id])
                return JsonResponse({
                    "razorpay_order_id": razorpay_order["id"],
                    "django_order_id": order.id,
                    "razorpay_merchant_key": settings.RAZOR_KEY_ID,
                    "razorpay_amount": amount,
                    "currency": "INR",
                    "callback_url": request.build_absolute_uri(callback_url),
                })
            else:
                return JsonResponse({"error": "Invalid payment method."}, status=400)

        except Exception as e:
            logger.error(f"Error in initiate_payment: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)


"""
CREATING ORDERS
"""
def create_order(request):
    try:
        cart_details = request.session.get('cart_details')
        if not cart_details:
            return JsonResponse({"error": "Cart details not found in session."}, status=400)

        user = request.user
        shipping_address_id = cart_details['shipping_address_id']
        payment_method = cart_details['payment_method']
        total_price = Decimal(cart_details['total_price'])
        cart_items = cart_details['cart_items']
        coupon_code = cart_details.get('coupon_code', None)
        coupon_discount = Decimal(cart_details.get('coupon_discount', '0.00'))

        # Fetch the shipping address
        shipping_address = ShippingAddress.objects.get(id=shipping_address_id, user=user)

        # Create the order
        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            payment_method=payment_method,
            total_price=total_price,
            payment_status='Paid' if payment_method != 'COD' else 'Pending',
            coupon=Coupon.objects.get(coupon_code=coupon_code) if coupon_code else None,
            discount_coupon_amount = coupon_discount,
            balance_refund = coupon_discount,
        )

        # Store order items
        for item in cart_items:
            product_variant = ProductVariant.objects.get(id=item['product_variant_id'])
            product = product_variant.product
            best_offer_price = product.best_offer_price if product.has_offer else product.price

            # Create a separate OrderItem for each quantity
            for _ in range(item['quantity']):
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_variant=product_variant,
                    quantity=1, 
                    price=best_offer_price,
                )
                # product_variant.stock -= 1  # Deduct stock for each quantity
                # product_variant.save()

        # Clear the cart
        cart = Cart.objects.get(user=user)
        CartItem.objects.filter(cart=cart).delete()

        # Record coupon usage
        if coupon_code:
            CouponUsage.objects.create(user=user, coupon=Coupon.objects.get(coupon_code=coupon_code))
            del request.session['coupon_code']

        # Clear the session
        del request.session['cart_details']

        return JsonResponse({"success": "Order created successfully."}, status=200)

    except Exception as e:
        logger.error(f"Error in create_order: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


"""
PAYMENT HANDLING IN BOTH INITIAL PAYMENT AND RETRY
"""
@csrf_exempt
def paymenthandler(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method.")

    try:
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        if not payment_id or not razorpay_order_id or not signature:
            messages.error(request, "Missing payment data.")
            return redirect('retry_payment', args=[django_order_id])

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            razorpay_order = razorpay_client.order.fetch(razorpay_order_id)
            django_order_id = razorpay_order['notes'].get('django_order_id')
            
            if not django_order_id:
                messages.error(request, "Order ID missing.")
                return redirect('retry_payment', args=[django_order_id])

            order = Order.objects.get(id=django_order_id)
        except (razorpay.errors.SignatureVerificationError, Order.DoesNotExist) as e:
            messages.error(request, str(e))
            return redirect('retry_payment', args=[django_order_id])

        cart = Cart.objects.get(user=order.user)
        CartItem.objects.filter(cart=cart).delete()

        payment = razorpay_client.payment.fetch(payment_id)

        if payment['status'] == 'captured':
            order.payment_status = 'Paid'
            order.status = 'pending'
            order.save()

            # Update order items status to 'order_placed'
            order_items = OrderItem.objects.filter(order=order)
            for item in order_items:
                item.status = 'order_placed'
                item.save()

            is_retry = razorpay_order.get('notes', {}).get('is_retry', False)

            if is_retry:
                return redirect('retry_order_success', order_id=order.id)
            else:
                return redirect('order_success', order_id=order.id)

        else:
            # Failure: Revert stock
            order_items = OrderItem.objects.filter(order=order)
            for item in order_items:
                product_variant = item.product_variant
                product_variant.stock += 1 
                product_variant.save()

        order.payment_status = 'Pending'
        order.retry_payment_attempts += 1
        order.save()
        messages.error(request, "Failed payment.")
        return redirect('retry_payment', order_id=order.id)

    except Exception as e:
        messages.error(request, str(e))
        return HttpResponseBadRequest()
        
# def paymenthandler(request):
#     if request.method == "POST":
#         try:
#             payment_id = request.POST.get('razorpay_payment_id', '')
#             razorpay_order_id = request.POST.get('razorpay_order_id', '')
#             signature = request.POST.get('razorpay_signature', '')
            
#             if not all([payment_id, razorpay_order_id, signature]):
#                 messages.error(request, "Payment verification failed: Missing parameters")
#                 return redirect('payment_failed')
            
#             params_dict = {
#                 'razorpay_order_id': razorpay_order_id,
#                 'razorpay_payment_id': payment_id,
#                 'razorpay_signature': signature
#             }

#             # Verify payment signature
#             razorpay_client.utility.verify_payment_signature(params_dict)
            
#             # Fetch order details from Razorpay
#             razorpay_order = razorpay_client.order.fetch(razorpay_order_id)
#             order_id = razorpay_order['notes']['django_order_id']
            
#             # Update order status
#             order = Order.objects.get(id=order_id)
#             order.payment_status = 'Paid'
#             order.status = 'pending'
#             order.save()

#             # Clear cart
#             cart = Cart.objects.get(user=order.user)
#             cart.items.all().delete()
            
#             return redirect('order_success', order_id=order.id)
            
#         except razorpay.errors.SignatureVerificationError:
#             messages.error(request, "Payment verification failed")
#             return redirect('payment_failed')
#         except Order.DoesNotExist:
#             messages.error(request, "Order not found")
#             return redirect('payment_failed')
#         except Exception as e:
#             messages.error(request, f"Payment processing error: {str(e)}")
#             return redirect('payment_failed')
    
#     return HttpResponseBadRequest()
    

"""
RETRY PAYMENT INITIALISATIOIN
"""
@csrf_exempt
def initiate_retry_payment(request):
    if request.method == "POST":
        try:
            retry_payment_details = request.session.get('retry_payment_details')
            if not retry_payment_details:
                logger.error("Retry payment details not found in session.")
                return JsonResponse({"error": "Retry payment details not found in session."}, status=400)

            user = request.user
            order_id = retry_payment_details['order_id']
            payment_method = retry_payment_details['payment_method']
            total_price = Decimal(retry_payment_details['total_price'])

            logger.debug(f"Retry Payment Details - Order ID: {order_id}, Payment Method: {payment_method}, Total Price: {total_price}")

            order = Order.objects.get(id=order_id, user=user)

            if payment_method == "razorpay":
                amount = int(total_price * 100)  # Convert to paise
                logger.debug(f"Amount to be charged in paise: {amount}")
                
                razorpay_order = razorpay_client.order.create({
                    "amount": amount,
                    "currency": "INR",
                    "receipt": f"order_{order.id}",
                    "notes": {
                        "django_order_id": order.id,
                        "user_id": user.id,
                        "is_retry": True
                    },
                })
                logger.debug(f"Razorpay Order Created: {razorpay_order}")
                
                return JsonResponse({
                    "razorpay_order_id": razorpay_order["id"],
                    "django_order_id": order.id,
                    "razorpay_merchant_key": settings.RAZOR_KEY_ID,
                    "razorpay_amount": amount,
                    "currency": "INR",
                    "callback_url": request.build_absolute_uri(reverse('retry_order_success', args=[order.id])),  # Pass order_id here
                })
            logger.error("Invalid payment method.")
            return JsonResponse({"error": "Invalid payment method."}, status=400)

        except Exception as e:
            logger.error(f"Error in initiate_retry_payment: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    logger.error("Invalid request method.")
    return JsonResponse({"error": "Invalid request method"}, status=405)
