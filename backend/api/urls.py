from django.urls import include, path
from rest_framework import routers
from api import views
from users.views import UserViewSet
from recipe.views import TagViewSet, IngredientViewSet, RecipeViewSet

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('<uuid:query>/', views.redirect, name='redirect')
]
