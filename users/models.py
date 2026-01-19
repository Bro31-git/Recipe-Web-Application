from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Avg
import re

# Create your models here.
class User(AbstractUser):
    #additional fields based on user roles
    is_chef = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    country = models.CharField(max_length=100, blank=True)
    saved_recipes = models.ManyToManyField('Recipe', related_name='saved_by', blank=True)

class ChefProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    years_of_experience = models.IntegerField(default=0)

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

    def get_video_id(self):
        """Extracts the ID from a YouTube URL to use in the player"""
        if not self.video_url:
            return None
        
        # This regex handles both 'youtube.com' and 'youtu.be' links
        regex = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
        match = re.search(regex, self.video_url)
        
        if match:
            return match.group(1)
        return None

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
