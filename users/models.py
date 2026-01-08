from django.db import models
from django.db.models import Avg
import re
# Create your models here.

class Recipe(models.Model):
    chef = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    origin_country = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    image = models.ImageField(upload_to='recipe_images/', blank=True, null=True)
    #stores the ingredients and instructions as a list of strings(JSONField)
    ingredients = models.JSONField(default=list, blank=True)
    instructions = models.JSONField(default=list, blank=True)
    health_condition = models.CharField(max_length=100, blank=True, null=True)
    dietary = models.CharField(max_length=100, blank=True, null=True)
    meal_type = models.CharField(max_length=100, blank=True, null=True)
    meal_time = models.CharField(max_length=100, blank=True, null=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=10, default='XAF')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    cooking_time = models.PositiveIntegerField(help_text="Time in minutes", default=30) 

    video_url = models.URLField(max_length=200, blank=True, null=True) 

    def get_average_rating(self):
        reviews = self.reviews.all() 
        
        if reviews.exists():
            # Calculate average of the 'rating' field
            return reviews.aggregate(Avg('rating'))['rating__avg']
        return 0
    

    def __str__(self):
        return self.title
    
class Review(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} on {self.recipe.title}"
