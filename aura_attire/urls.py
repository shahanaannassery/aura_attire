"""
URL configuration for aura_attire project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', include('home.urls')),
    path('admin/', admin.site.urls),
    path('user/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('', include('user_profile.urls')),
    path('shop/', include('shop.urls')),
    path('adminpanel/', include('admin_side.urls')),  
    path('products/',include('products.urls')),
    path('category/', include('category.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('coupons/', include('couponsapp.urls')),
    path('wallet/', include('wallet.urls')),
    path('offers/', include('offers.urls')),
    path('wishlist/', include('wishlist.urls')),
    path('payments/', include('payments.urls')),
    # path('review/', include('reviews.urls')),
]
urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)