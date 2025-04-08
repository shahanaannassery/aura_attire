from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Wallet, WalletTransaction
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
"""
WALLET PAGE
"""
@login_required
def wallet_view(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        # If the wallet does not exist, create a new one with zero balance
        wallet = Wallet.objects.create(user=request.user, balance=0.00)
    
    # Filter
    filter_type = request.GET.get('filter', 'all') 
    
    # Filter transactions based on the selected filter
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')
    if filter_type == 'credit':
        transactions = transactions.filter(transaction_type='credit')
    elif filter_type == 'debit':
        transactions = transactions.filter(transaction_type='debit')
    
    page = request.GET.get('page', 1) 
    paginator = Paginator(transactions, 10)
    
    try:
        transactions = paginator.page(page)
    except PageNotAnInteger:
        transactions = paginator.page(1)
    except EmptyPage:
        transactions = paginator.page(paginator.num_pages)
    
    return render(request, 'user/wallet.html', {
        'wallet': wallet,
        'transactions': transactions,
        'filter_type': filter_type,
    })




"""
ADMIN WALLET TRANSACTIONS
"""
@staff_member_required
def admin_wallet_transactions(request):
    # Filter
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('search', '')
    
    # Get all wallet transactions
    transactions = WalletTransaction.objects.select_related('wallet__user', 'order').order_by('-created_at')
    
    # Apply filters
    if filter_type == 'credit':
        transactions = transactions.filter(transaction_type='credit')
    elif filter_type == 'debit':
        transactions = transactions.filter(transaction_type='debit')
    
    # Apply search
    if search_query:
        transactions = transactions.filter(
            Q(wallet__user__username__icontains=search_query) |
            Q(wallet__user__email__icontains=search_query) |
            Q(order__id__icontains=search_query) |
            Q(id__icontains=search_query)

        )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(transactions, 10)
    
    try:
        transactions = paginator.page(page)
    except PageNotAnInteger:
        transactions = paginator.page(1)
    except EmptyPage:
        transactions = paginator.page(paginator.num_pages)
    
    return render(request, 'admin/wallet_transactions.html', {
        'transactions': transactions,
        'filter_type': filter_type,
        'search_query': search_query,
    })

"""
ADMIN WALLET TRANSACTION DETAIL
"""


@staff_member_required
def admin_wallet_transaction_detail(request, transaction_id):
    transaction = get_object_or_404(
        WalletTransaction.objects.select_related('wallet__user', 'order'), 
        id=transaction_id
    )
    return render(request, 'admin/wallet_transaction_detail.html', {
        'transaction': transaction,
    })