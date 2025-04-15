
from django.shortcuts import render, HttpResponse
from category.models import Category
from products.models import ProductWithImages
import random
from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.conf import settings
from .forms import ContactForm

# Create your views here.


"""
HOME PAGE
"""
def index(request):
    categories = Category.objects.filter(is_listed=True)

    #Fetch the latest 4 products 
    latest_products = ProductWithImages.objects.filter(is_listed=True).order_by('-created_at')[:4] 

    #Randomly shuffle the products to show them in random order
    random_products = random.sample(list(latest_products), len(latest_products))

    context = {
        'categories': categories,
        'random_products': random_products,
    }
    
    return render(request, 'user/home.html',context)




"""
ABOUT PAGE
"""
def about(request):
    return render(request, 'user/about.html')


"""
CONTACT US PAGE
"""
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            email_message = EmailMessage(
                subject=f"Contact Form: {subject}",
                body=f"Message from {name} ({email}):\n\n{message}",
                from_email=email, 
                to=[settings.CONTACT_EMAIL],
                reply_to=[email],
            )

            email_message.send()

            return redirect('contact_success')
    else:
        form = ContactForm()

    return render(request, 'user/contact.html', {'form': form})


"""
CONTACT SUCCESS PAGE
"""
def contact_success(request):
    return render(request, 'user/contact_success.html')