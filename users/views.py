from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Recipe
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, TextField
from django.db.models.functions import Cast
from django.views.generic.edit import FormMixin
from .forms import  RecipeForm, ReviewForm
from django.urls import reverse_lazy, reverse
import json
from django.contrib import messages

# Create your views here.
def toggle_recipe_save(request, pk):
    #checks if the user is authenticated and  logged in
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)

    recipe = get_object_or_404(Recipe, pk=pk)# get recipe object or return a 404 eror message
    user = request.user# get the current login user
    if user.saved_recipes.filter(pk=pk).exists():# check the status of the saved recipe button
        user.saved_recipes.remove(recipe)
        saved = False
    else:
        user.saved_recipes.add(recipe)
        saved = True
    # return JSON response indicating the new saved status
    return JsonResponse({'saved': saved, 'recipe_title': recipe.title})# return the status to the js about the save button


def recommendation(request):
    if request.method == 'POST':
        #getting the corresponding form data
        h_cond = request.POST.get('health_condition') 
        diet = request.POST.get('dietary')      # Fixed: Matches name="dietary"
        allergies = request.POST.get('allergies') # Matches name="allergies"

        #
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

class RecipeDetailView(FormMixin, DetailView):
    model = Recipe
    template_name = 'users/recipe_detail.html'
    context_object_name = 'recipe'
    form_class = ReviewForm 

    def get_success_url(self):# redirect to the same recipe detail page after form submission
        return reverse('recipe-detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):# add extra context data to the template for ingredients and instructions
        context = super().get_context_data(**kwargs)# get the existing context data
        context['form'] = self.get_form()# add the review form to the context
        
        raw_ing = self.object.ingredients# get the raw ingredients data
        # 1. Ingredients
        if isinstance(raw_ing, list):# if it's already a list, use it directly
            context['ingredients_list'] = raw_ing# assign to context
        elif isinstance(raw_ing, str):# if it's a string, try to parse it as JSON
            try:
                context['ingredients_list'] = json.loads(raw_ing)# parse JSON string to list
            except (json.JSONDecodeError, TypeError):# handle parsing errors
                context['ingredients_list'] = [{'name': raw_ing, 'qty': ''}] # Fallback

        # 2. Instructions
        raw_inst = self.object.instructions# get the raw instructions data
        if isinstance(raw_inst, list):# if it's already a list, use it directly
            context['instructions_list'] = raw_inst# assign to context
        elif isinstance(raw_inst, str):# if it's a string, try to parse it as JSON
            try:
                context['instructions_list'] = json.loads(raw_inst)# parse JSON string to list
            except (json.JSONDecodeError, TypeError):# handle parsing errors
                context['instructions_list'] = [raw_inst] # Fallback

        return context# return the final context data

    # Handle POST request for submitting reviews
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
            
        self.object = self.get_object()# get the current recipe object
        form = self.get_form()# get the review form
        
        if form.is_valid():# if the form is valid
            return self.form_valid(form)# process the valid form
        else:
            return self.form_invalid(form)
    # process valid form submission
    def form_valid(self, form):
        review = form.save(commit=False)# create review instance without saving to database yet
        review.recipe = self.object# link review to the current recipe
        review.user = self.request.user# link review to the logged-in user
        review.save()# save the review to the database
        messages.success(self.request, "Review submitted!")
        return super().form_valid(form)# continue with the default form valid processing


    