"""
URL configuration for recipe_journal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from recipe_journal.views.api import add_ingredient_form, add_to_collection, add_recipe_history, check_collection_status
from recipe_journal.views.api import check_title, remove_from_collection,  remove_recipe_history
from recipe_journal.views.web import add_recipe, login, logout, modify_profile, register, search_recipe
from recipe_journal.views.web import show_friends, show_recipe, show_recipe_collection, show_confirmation_page
from recipe_journal.views.web import welcome

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", welcome),
    path("add-recipe", add_recipe),
    path("api/add-ingredient-form", add_ingredient_form),
    path("api/add-to-collection", add_to_collection),
    path("api/add-recipe-history", add_recipe_history),
    path("api/check-collection-status", check_collection_status),
    path("api/check-title", check_title),
    path("api/remove-from-collection", remove_from_collection),
    path("api/remove-recipe-history", remove_recipe_history),
    path("login", login),
    path("logout", logout),
    path("modify-profile", modify_profile),
    path("register", register),
    path("search-recipe", search_recipe),
    path("show-confirmation-page", show_confirmation_page),
    path("show-friends", show_friends),
    path("show-recipe", show_recipe),
    path("show-recipe-collection", show_recipe_collection),
    path("welcome", welcome),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
