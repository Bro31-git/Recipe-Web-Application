from django.urls import path

from . import views
from .views import (
    RecipeListView, 
    RecipeDetailView, 
    RecipeCreateView, 
    RecipeUpdateView, 
    RecipeDeleteView
)

urlpatterns = [

    path('dashboard/', RecipeListView.as_view(), name='dashboard'),
    path('recipe/<int:pk>/save/', views.toggle_recipe_save, name='toggle-save'),
    path('recommendation/', views.recommendation, name='recommendation'),
    path('reset-filters/', views.reset_filters, name='reset_filters'),
    path('recipe/new/', RecipeCreateView.as_view(), name='recipe_create'),
    path('recipe/<int:pk>/', RecipeDetailView.as_view(), name='recipe-detail'),
    path('recipe/<int:pk>/update/', RecipeUpdateView.as_view(), name='recipe-update'),
    path('recipe/<int:pk>/delete/', RecipeDeleteView.as_view(), name='recipe-delete'),


]