from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from recipes.models import Recipe
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, TextField
from django.db.models.functions import Cast

# Create your views here.
def toggle_recipe_save(request, pk):
    #checks if the user is authenticated and  logged in
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)

    recipe = get_object_or_404(Recipe, pk=pk)
    user = request.user
    if user.saved_recipes.filter(pk=pk).exists():
        user.saved_recipes.remove(recipe)
        saved = False
    else:
        user.saved_recipes.add(recipe)
        saved = True
    # return JSON response indicating the new saved status
    return JsonResponse({'saved': saved, 'recipe_title': recipe.title})


def recommendation(request):
    if request.method == 'POST':
        #getting the corresponding form data
        h_cond = request.POST.get('health_condition') 
        diet = request.POST.get('dietary')      # Fixed: Matches name="dietary"
        allergies = request.POST.get('allergies') # Matches name="allergies"

        request.session['temp_filters'] = {
            'health_condition': h_cond,
            'dietary': diet,
            'allergies': allergies 
        }
        
        return redirect('dashboard')

    return render(request, 'users/recommendation.html')

def reset_filters(request):
    if 'temp_filters' in request.session:
        del request.session['temp_filters']
    return redirect('dashboard')

class RecipeListView(LoginRequiredMixin, ListView):
    model = Recipe# model or database wo be use in this view
    template_name = 'users/dashboard.html'# template name to redirect info to
    context_object_name = 'recipes'# custom object name you will use
    ordering = ['-created_at']# display element as from the recent to the oldest

    def get_queryset(self):
        queryset = super().get_queryset()# create a query set to take all info to be filter

        queryset = queryset.annotate(ingredient_str = Cast('ingredients', TextField()))# casting the json data into a string to be able to loop through it
        session_filters = self.request.session.get('temp_filters', None)
        self.is_recommendation_active = False# set recommendation to false by default to False

        if session_filters:
            h_cond = session_filters.get('health_condition')
            diet = session_filters.get('dietary')
            allergies_text = session_filters.get('allergies')

            # Filter by Health
            if h_cond and h_cond not in ['None', '', 'Select']:
                queryset = queryset.filter(health_condition=h_cond)
                self.is_recommendation_active = True
            
            # Filter by Diet
            if diet and diet not in ['None', '', 'Select']:
                queryset = queryset.filter(dietary=diet)
                self.is_recommendation_active = True

            # Excluse allergies
            if allergies_text:
                self.is_recommendation_active = True
                raw_allergens = [a.strip().lower() for a in allergies_text.split(',') if a.strip()]# saparating each ingredient and converting it to lowercase
                final_allergens = []
                #loop to check if allergens are in raw allergen and also verify if it in plural
                for allergen in raw_allergens:
                    final_allergens.append(allergen)
                    if allergen.endswith('s'):
                        final_allergens.append(allergen[:-1])
                    if allergen.endswith('es'):
                        final_allergens.append(allergen[:-2])
                #exclude all ingredients with the allergen
                for allergen in final_allergens:
                    queryset = queryset.exclude(ingredients_str__icontains=allergen)
            
            # 2. Search & Filters (GET request)
        query = self.request.GET.get('q')#search query parameter
        if query:# if a search query is provided
            queryset = queryset.filter(#search in title, description, and origin country
                Q(title__icontains=query) | # case-insensitive contains 
                Q(description__icontains=query) | # case-insensitive contains
                Q(origin_country__icontains=query)
            )

        dietary_query = self.request.GET.get('dietary')# dietary filter parameter
        if dietary_query:# if a dietary filter is provided
            queryset = queryset.filter(dietary=dietary_query)# filter by dietary
        
        min_price = self.request.GET.get('min_price')# minimum price filter parameter
        max_price = self.request.GET.get('max_price')# maximum price filter parameter
        try:
            if min_price: 
                queryset = queryset.filter(budget__gte=float(min_price))# filter by minimum budget
            if max_price: 
                queryset = queryset.filter(budget__lte=float(max_price))# filter by maximum budget
        except ValueError:
            pass # If they typed text instead of numbers, simply ignore the filter

        meal_times = self.request.GET.getlist('meal_time')
        if meal_times: #
            queryset = queryset.filter(meal_time__in=meal_times)

        meal_types = self.request.GET.getlist('meal_type')# verity if the mealtype was checked by the user
        if meal_types: 
            queryset = queryset.filter(meal_type__in=meal_types)# if present attach it to the query set

        return queryset# return the final filtered queryset

    def get_context_data(self, **kwargs):# add extra context data to the template
        context = super().get_context_data(**kwargs)
        context['is_filtered'] = getattr(self, 'is_recommendation_active', False)
        return context


