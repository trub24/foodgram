from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.http.response import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.decorators import action
from recipe.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    IngredientAmount
)
from api.filters import RecipeFilter, IngredientFilter
from api.permissions import IsAuthorOrReadOnlyPermission
from recipe.serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeCreateSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
)


class ListRetrieveViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [AllowAny, ]
    pagination_class = None


class TagViewSet(ListRetrieveViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ListRetrieveViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthorOrReadOnlyPermission]
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=['get'],
            url_path=r'(?P<recipe_id>\d+)/get-link',
            url_name='get-link',
            permission_classes=[AllowAny],
            detail=False)
    def get_link(self, request, recipe_id):
        recipe = Recipe.objects.get(id=recipe_id)
        short_link = recipe.short_link
        response = JsonResponse({
            'short-link': f'{short_link}',
        })
        return response

    @action(methods=['post', 'delete'],
            url_path=r'(?P<recipe_id>\d+)/favorite',
            url_name='favorite',
            permission_classes=[IsAuthenticated],
            detail=False)
    def favorite(self, request, recipe_id):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            favorite = Favorite.objects.create(user=user, recipe=recipe)
            serializer = FavoriteSerializer(favorite, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                favorite = Favorite.objects.get(user=user, recipe=recipe)
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post', 'delete'],
            url_path=r'(?P<recipe_id>\d+)/shopping_cart',
            url_name='shopping_cart',
            permission_classes=[IsAuthenticated],
            detail=False)
    def shopping_cart(self, request, recipe_id):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=user, recipe=recipe
            ).exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            sh_cart = ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = ShoppingCartSerializer(sh_cart, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if ShoppingCart.objects.filter(
                user=user, recipe=recipe
            ).exists():
                sh_cart = ShoppingCart.objects.get(
                    user=user, recipe=recipe
                )
                sh_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'],
            url_path='download_shopping_cart',
            url_name='download_shopping_cart',
            permission_classes=[IsAuthenticated],
            detail=False)
    def download_shopping_cart(self, request):
        user = self.request.user
        ingredients = IngredientAmount.objects.filter(
            recipe__shopping_cart__user=user
        ).values('ingredient__name', 'ingredient__measurement_unit').annotate(
            amount=Sum('amount')
        )
        list_for_sh = ['Список покупок\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            amount = ingredient['amount']
            unit = ingredient['ingredient__measurement_unit']
            list_for_sh += [
                f'{name} {amount} {unit}\n'
            ]
        return FileResponse(
            list_for_sh, as_attachment=True, filename="Shopping-list.txt"
        )
