from django.urls import path
from .views import (wallet_view, admin_wallet_transactions,
    admin_wallet_transaction_detail)

urlpatterns = [
    path('', wallet_view, name='wallet_view'),
     
   # Admin wallet URLs
    path('admin/', admin_wallet_transactions, name='admin_wallet_transactions'),
    path('admin/<int:transaction_id>/',admin_wallet_transaction_detail, name='admin_wallet_transaction_detail'),
]