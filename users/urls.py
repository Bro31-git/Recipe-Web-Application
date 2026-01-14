# users/urls.py
from django.views.generic import TemplateView
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import (
    RecipeListView, 
    RecipeDetailView, 
    RecipeCreateView, 
    RecipeUpdateView, 
    RecipeDeleteView
)

urlpatterns = [
    path('select/', views.signup_selection, name='signup-select'),
    path('signup/chef/', views.chef_signup, name='chef-signup'),
    path('signup/user/', views.customer_signup, name='user-signup'),
    path('login/', views.login_view, name='login'),
    path('api/check-account/', views.check_account_ajax, name='check-account'),
    path('api/reset-password/', views.reset_password_ajax, name='reset-password'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', RecipeListView.as_view(), name='dashboard'),
    # Add this line to your existing urlpatterns
    path('recipe/<int:pk>/save/', views.toggle_recipe_save, name='toggle-save'),
    path('recommendation/', views.recommendation, name='recommendation'),
    path('reset-filters/', views.reset_filters, name='reset_filters'),
    # CRUD Operations
    path('recipe/new/', RecipeCreateView.as_view(), name='recipe_create'),
    path('recipe/<int:pk>/', RecipeDetailView.as_view(), name='recipe-detail'),
    path('recipe/<int:pk>/update/', RecipeUpdateView.as_view(), name='recipe-update'),
    path('recipe/<int:pk>/delete/', RecipeDeleteView.as_view(), name='recipe-delete'),

    path('about/', TemplateView.as_view(template_name='users/about.html'), name='about'),
    path('terms_chef/', TemplateView.as_view(template_name='users/terms_chef.html'), name='terms-chef'),
    path('terms_user/', TemplateView.as_view(template_name='users/terms_user.html'), name='terms-user'),
]