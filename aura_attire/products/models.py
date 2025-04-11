from django.db import models
import cloudinary.models
from category.models import Category

class ProductWithImages(models.Model):
    name = models.CharField(max_length=500)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_listed = models.BooleanField(default=False)

    # Cloudinary fields for images
    image1 = cloudinary.models.CloudinaryField('image1')
    image2 = cloudinary.models.CloudinaryField('image2')
    image3 = cloudinary.models.CloudinaryField('image3')

    def __str__(self):
        return self.name



class ProductVariant(models.Model):
    product = models.ForeignKey(ProductWithImages, on_delete=models.CASCADE, related_name='variants')
    color = models.CharField(max_length=50)
    size = models.CharField(max_length=50)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'color', 'size')  # Prevent duplicates

    def __str__(self):
        return f"{self.product.name} - {self.color} - {self.size}"