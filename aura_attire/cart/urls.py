from django.urls import path
from . import views
from .views import update_cart, remove_from_cart

urlpatterns = [
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('update_cart/<int:item_id>/<str:action>/', update_cart, name='update_cart'),
    path('remove_from_cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
]