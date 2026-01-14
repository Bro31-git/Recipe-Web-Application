import json# convert between JSON strings and Python lists
from django.shortcuts import render, redirect, get_object_or_404# returns , redirect and get object or 404 error
from django.contrib import messages# message framework for user feedback
from django.contrib.auth import authenticate, login, logout# login and removes a user session
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin# blocks access to views based on authentication and user permissions
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView# display lists, details, create, update, delete views
from django.views.generic.edit import FormMixin# mixin to add form handling to detail views used to submit reviews
from django.urls import reverse_lazy, reverse# for URL resolution (lazy and immediate )
from django.http import JsonResponse# for returning JSON responses used in saving recipes
from django.db.models import Q, TextField# complex queries with OR conditions used for search functionality
from django.db.models.functions import Cast# cast fields to different types for querying
from .models import Recipe
from django.contrib.auth.models import User
from .forms import ChefSignUpForm, UserSignUpForm, LoginForm, RecipeForm, ReviewForm

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

def terms_chef(request):
    return render(request, 'users/terms_chef.html')

def terms_user(request):
    return render(request, 'users/terms_user.html')
# --- AUTH VIEWS ---
def signup_selection(request):
    return render(request, 'users/signup_selection.html')

def chef_signup(request):
    if request.method == 'POST':
        form = ChefSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Chef Account created for {username}! Please Login.')
            return redirect('login')
    else:
        form = ChefSignUpForm()
    return render(request, 'users/chef_signup.html', {'form': form})

def customer_signup(request):
    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserSignUpForm()
    return render(request, 'users/user_signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":
        # Check if the request is AJAX (JSON body)
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            login_val = data.get('username') # This could be username or email
            password = data.get('password')
            
            # Step 1: Find the user by username OR email
            user_obj = User.objects.filter(Q(username=login_val) | Q(email=login_val)).first()
            
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)
                if user is not None:
                    login(request, user)
                    return JsonResponse({"message": "Success", "redirect_url": "/dashboard/"}, status=200)
            
            return JsonResponse({"message": "Invalid username/email or password"}, status=401)

        else:
            # Standard Django Form Fallback
             # Ensure you have this in forms.py
            form = LoginForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid credentials.")
                return render(request, "users/login.html", {'form': form})

    return render(request, "users/login.html")

def check_account_ajax(request):
    #"""Checks if account exists via Username or Email"""
    if request.method == "POST":
        data = json.loads(request.body)
        identifier = data.get('identifier', '').strip() # Enter email or username
        
        user_exists = User.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier)).exists()
        
        if user_exists:
            # We return the email so the JS can use it as a primary key for the next step
            user = User.objects.get(Q(username__iexact=identifier) | Q(email__iexact=identifier))
            return JsonResponse({"exists": True, "email": user.email}, status=200)
            
        return JsonResponse({"exists": False, "message": "Account not found."}, status=404)

def reset_password_ajax(request):
   #"""Final password update"""
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get('email')
        new_password = data.get('password')
        
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            return JsonResponse({"message": "Password updated successfully"}, status=200)
        except User.DoesNotExist:
            return JsonResponse({"message": "An error occurred"}, status=400)

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

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

class RecipeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Recipe
    success_url = reverse_lazy('dashboard')

    def test_func(self):
        recipe = self.get_object()# get the current recipe object
        return self.request.user == recipe.chef# check if the logged-in user is the chef of the recipe


class RecipeCreateView(LoginRequiredMixin, CreateView):
    model = Recipe# table where data will be saved
    form_class = RecipeForm# form to be used for creating a recipe
    template_name = 'users/recipe_form.html'
    success_url = reverse_lazy('dashboard')# redirect to dashboard after successful creation

    # verify if the info pass it is valid then we override it with our custom rules
    def form_valid(self, form):
        recipe = form.save(commit=False)# create recipe instance without saving to database yet
        #check if whether the recipe does not yet exist in the database
        if not recipe.pk: #assign the logged-in user as the chef for new recipes
            recipe.chef = self.request.user
        
        ing_data = form.cleaned_data.get('ingredients')# get cleaned ingredients data
        inst_data = form.cleaned_data.get('instructions')# get cleaned instructions data
   
        if ing_data:
            if isinstance(ing_data, list):# if it's already a list, convert to JSON string
                recipe.ingredients = json.dumps(ing_data)# convert list to JSON string
            else:
                try:
                    # Clean/Format the JSON string
                    parsed = json.loads(ing_data)# parse JSON string to list
                    recipe.ingredients = json.dumps(parsed)# convert back to JSON string
                except json.JSONDecodeError:
                    recipe.ingredients = json.dumps([ing_data])# wrap in list and convert to JSON string
        else:
            recipe.ingredients = "[]"# empty JSON array if no data provided

        # Handle Instructions
        if inst_data:
            if isinstance(inst_data, list):# check if the data is already a list
                recipe.instructions = json.dumps(inst_data)# convert list to JSON string
            else:
                try:
                    parsed = json.loads(inst_data)# parse JSON string to list
                    recipe.instructions = json.dumps(parsed)# convert back to JSON string
                except json.JSONDecodeError:
                    recipe.instructions = json.dumps([inst_data])# wrap in list and convert to JSON string
        else:
            recipe.instructions = "[]"# empty JSON array if no data provided

        
        diet_val = form.cleaned_data.get('dietary')
        if diet_val == 'None':
            recipe.dietary = ''  # Save as empty string in DB so as to revent it from saving none
        else:
            recipe.dietary = diet_val

        health_val = form.cleaned_data.get('health_condition')
        if health_val == 'None':
            recipe.health_condition = '' # Save as empty string in DB so as to revent it from saving none
        else:
            recipe.health_condition = health_val 
        recipe.save()# save the recipe to the database
        return redirect(self.success_url)# redirect to the success URL
    
class RecipeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Recipe
    form_class = RecipeForm
    template_name = 'users/recipe_form.html'
    success_url = reverse_lazy('dashboard')


    def test_func(self):# check if the logged-in user is the chef of the recipe
        recipe = self.get_object()
        return self.request.user == recipe.chef# if true, allow access otherwise deny
    
    
    def form_valid(self, form):
        recipe = form.save(commit=False)# create recipe instance without saving to database yet
        # Only set chef if it's the CreateView
        if not recipe.pk: #assign the logged-in user as the chef for new recipes
            recipe.chef = self.request.user
        
        ing_data = form.cleaned_data.get('ingredients')# get cleaned ingredients data currently added by the chef
        inst_data = form.cleaned_data.get('instructions')# get cleaned instructions data currently added by the chef

        # saving ingredient data as a json file in the db
        if ing_data:
            if isinstance(ing_data, list):# if it's already a list, convert to JSON string
                recipe.ingredients = json.dumps(ing_data)#  convert list to JSON string
            else:
                try:
                    #if it is in string 
                    parsed = json.loads(ing_data)# parse JSON string to list
                    recipe.ingredients = json.dumps(parsed)# convert back to JSON string
                except json.JSONDecodeError:
                    recipe.ingredients = json.dumps([ing_data])# wrap in list and convert to JSON string
        else:
            recipe.ingredients = "[]"
        # saving instruction data as a json file in the db
        if inst_data:
            if isinstance(inst_data, list):# if it's already a list, convert to JSON string
                recipe.instructions = json.dumps(inst_data)#  convert list to JSON string
            else:
                try:
                    #if it is in string 
                    parsed = json.loads(inst_data)# parse JSON string to list
                    recipe.instructions = json.dumps(parsed)# convert back to JSON string
                except json.JSONDecodeError:
                    recipe.instructions = json.dumps([inst_data])# wrap in list and convert to JSON string
        else:
            recipe.instructions = "[]"# saving an empty set to the db

        recipe.save()# save the data to the db after adding custom logic to it for validation
        return redirect(self.success_url)# redirect to the success URL
