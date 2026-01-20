from django.contrib import admin
from .models import User
from .models import ChefProfile,Recipe

# Register your models here.
admin.site.register(User)
admin.site.register(ChefProfile)

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'chef', 'origin_country', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('origin_country', 'meal_type', 'created_at')