from .models import Recipe
from .models import Review
from django import forms


class RecipeForm(forms.ModelForm):
   
    dietary = forms.ChoiceField(
        choices=DIET_CHOICES, 
        required=False  # This prevent the app from crashing on an empty selection
    )
    health_condition = forms.ChoiceField(
        choices=HEALTH_CHOICES, 
        required=False # This prevent the app from crashing on an empty selection
    )

    class Meta:
        model = Recipe
        fields = ['title', 'description', 'image', 'video_url', 'cooking_time', 'dietary', 'health_condition', 'ingredients', 'instructions', 'budget', 'meal_type', 'origin_country']
        widgets = {
            'ingredients': forms.HiddenInput(),
            'instructions': forms.HiddenInput(),
        }




class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'content']