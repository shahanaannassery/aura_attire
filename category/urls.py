from django.urls import path
from . import views

urlpatterns = [
    path("management/",views.category_management,name='category_management'),
    path('edit/<int:category_id>',views.edit_category,name='edit_category'),
    path('toggle/<int:category_id>',views.toggle_listing,name='toggle_listing')
]