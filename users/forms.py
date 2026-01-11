from .models import Recipe
from .models import Review
from django import forms
from django.core.exceptions import ValidationError 

DIET_CHOICES = [
    ('', 'Select Preference'),
    ('Vegetarian', 'Vegetarian (No Meat)'),
    ('Vegan', 'Vegan (No Animal Products)'),
    ('Gluten-Free', 'Gluten-Free'),
    ('Dairy-Free', 'Dairy-Free / Lactose-Free'),
    ('Halal', 'Halal'),
    ('Kosher', 'Kosher'),
    ('Keto', 'Keto / Low Carb'),
    ('Nut-Free', 'Nut-Free (Allergy Safe)'),
    ('Shellfish-Free', 'Shellfish-Free'),
    ('Pescatarian', 'Pescatarian (Fish Allowed)'),
    ('None', 'None'),
]

HEALTH_CHOICES = [
    ('', 'Select Condition'),
    ('Diabetes', 'Diabetes (Low Sugar/Carb)'),
    ('Hypertension', 'Hypertension (Low Sodium)'),
    ('Heart Disease', 'Heart Disease (Low Cholesterol)'),
    ('Celiac', 'Celiac Disease (Strict No Gluten)'),
    ('GERD', 'GERD / Acid Reflux'),
    ('IBS', 'IBS (Low FODMAP)'),
    ('Kidney Disease', 'Kidney Disease (Renal Diet)'),
    ('Obesity', 'Weight Loss / Low Calorie'),
    ('Gout', 'Gout (Low Purine)'),
    ('Anemia', 'Anemia (High Iron)'),
    ('None', 'None'),
]

class RecipeForm(forms.ModelForm):
   
    dietary = forms.ChoiceField(
        choices=DIET_CHOICES, 
        required=False  # This prevent the app from crashing on an empty selection
    )
    health_condition = forms.ChoiceField(
        choices=HEALTH_CHOICES, 
        required=False # This prevent the app from crashing on an empty selection
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

         # Check if we are editing an existing recipe
        if self.instance and self.instance.pk:
            #converting the python list ingredient gotten from the db to a json file to be display for editing
            if isinstance(self.instance.ingredients, list):
                # using dumps() to add a double quotes to the list 
                self.fields['ingredients'].initial = json.dumps(self.instance.ingredients)

            #converting the python list instruction gotten from the db to a json file to be display for editing
            if isinstance(self.instance.instructions, list):
                # using dumps() to add a double quotes to the list 
                self.fields['instructions'].initial = json.dumps(self.instance.instructions)
            


    class Meta:
        model = Recipe
        fields = ['title', 'description', 'image', 'video_url', 'cooking_time', 'dietary', 'health_condition', 'ingredients', 'instructions', 'budget', 'meal_type', 'origin_country']
        widgets = {
            'ingredients': forms.HiddenInput(),
            'instructions': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        selected_diet = cleaned_data.get('dietary')
        selected_health = cleaned_data.get('health_condition')
        ing_data = cleaned_data.get('ingredients')

        if selected_diet in [None, '', 'None'] and selected_health in [None, '', 'None']:
            return cleaned_data
        if not ing_data:
            return cleaned_data
        
        ingredient_blob = str(ing_data).lower()

        restrictions = {
            # --- DIETARY  ---
            'vegan': ['chicken', 'beef', 'pork', 'meat', 'fish', 'egg', 'milk', 'cheese', 'honey', 'yogurt', 'butter', 'cream', 'gelatin', 'whey'],
            'vegetarian': ['chicken', 'beef', 'pork', 'meat', 'fish', 'tuna', 'salmon', 'shrimp', 'crab', 'gelatin'],
            'pescatarian': ['chicken', 'beef', 'pork', 'lamb', 'bacon', 'ham', 'sausage'],
            'halal': ['pork', 'bacon', 'ham', 'lard', 'wine', 'beer', 'alcohol', 'rum', 'liqueur', 'gelatin'],
            'kosher': ['pork', 'bacon', 'ham', 'shrimp', 'crab', 'lobster', 'clam', 'oyster', 'cheeseburger'],
            'keto': ['sugar', 'rice', 'pasta', 'bread', 'flour', 'potato', 'corn', 'syrup', 'banana', 'apple', 'candy', 'soda'], 
            'gluten-free': ['wheat', 'barley', 'rye', 'flour', 'bread', 'pasta', 'couscous', 'malt', 'soy sauce', 'seitan', 'beer'], 
            'dairy-free': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey', 'casein', 'lactose', 'ghee'],
            'nut-free': ['peanut', 'almond', 'walnut', 'cashew', 'pecan', 'hazelnut', 'macadamia', 'pistachio', 'nutella'],
            'shellfish-free': ['shrimp', 'crab', 'lobster', 'prawn', 'mussel', 'oyster', 'clam', 'scallop', 'squid'],

            # --- HEALTH CONDITIONS ---
            'diabetes': ['sugar', 'syrup', 'candy', 'chocolate', 'cake', 'soda', 'honey', 'molasses', 'jam', 'jelly', 'white rice'],
            'hypertension': ['salt', 'soy sauce', 'sodium', 'bacon', 'pickle', 'canned', 'salami', 'sausage', 'msg'], 
            'heart disease': ['butter', 'cream', 'bacon', 'lard', 'sausage', 'fried', 'coconut oil', 'palm oil'], 
            'celiac': ['wheat', 'barley', 'rye', 'flour', 'bread', 'pasta', 'soy sauce', 'malt', 'beer'],
            'gerd': ['spicy', 'chili', 'jalapeno', 'pepper', 'hot sauce', 'tomato', 'lemon', 'orange', 'coffee', 'chocolate', 'mint', 'garlic', 'onion'], 
            'ibs': ['onion', 'garlic', 'milk', 'wheat', 'beans', 'lentils', 'apple', 'pear', 'honey', 'mushroom'],
            'kidney disease': ['salt', 'banana', 'potato', 'spinach', 'avocado', 'tomato', 'brown rice', 'milk', 'yogurt'],
            'gout': ['liver', 'kidney', 'anchovy', 'sardine', 'herring', 'beer', 'beef', 'pork', 'shellfish', 'sugar'], 
        }

        errors = []

        # 4. VALIDATE DIET (Single Check)
        if selected_diet and selected_diet not in ['', 'None']:
            tag_key = selected_diet.lower() 
            if tag_key in restrictions:
                forbidden = restrictions[tag_key]
                found = [word for word in forbidden if word in ingredient_blob]
                if found:
                    errors.append(f" Conflict! You selected '{selected_diet}', but ingredients mention: {', '.join(set(found))}.")

        # 5. VALIDATE HEALTH (Single Check)
        if selected_health and selected_health not in ['', 'None']:
            tag_key = selected_health.lower()
            if tag_key in restrictions:
                forbidden = restrictions[tag_key]
                found = [word for word in forbidden if word in ingredient_blob]
                if found:
                    errors.append(f" Health Warning! '{selected_health}' typically avoids: {', '.join(set(found))}.")

        if errors:
            raise ValidationError(errors)

        return cleaned_data 



class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'content']