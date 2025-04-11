from django.contrib import admin
from .models import Address, Referral, ShippingAddress


# Register your models here.
admin.site.register(Referral)
admin.site.register(Address)
admin.site.register(ShippingAddress)