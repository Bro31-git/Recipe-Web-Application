from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from recipes.models import Recipe
from django.shortcuts import redirect

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
