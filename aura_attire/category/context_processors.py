from category.models import Category

def categories_context(request):
    categories = Category.objects.filter(is_listed=True)
    return {
        'categories': categories
    }