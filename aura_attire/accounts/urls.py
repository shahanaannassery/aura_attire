from django.urls import path
from . import views

urlpatterns = [
    # User Authentication
    path("login/", views.user_login, name='userlogin'),
    path("logout/", views.user_logout, name='userlogout'),
    
    # Registration
    path("register/", views.register, name='register'),
    path('otp/verify/', views.verify_otp, name='verify_otp'),
    path('otp/resend/', views.resend_otp, name='resend_otp'),

    # Forgot Password
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-forgot-password-otp/', views.verify_forgot_password_otp, name='verify_forgot_password_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
]