from django.urls import path
from . import views

urlpatterns = [
    path('all/', views.all_products, name='all_products'),
]