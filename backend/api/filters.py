import django_filters as filters
from recipe.models import Recipe, Tag, Ingredient


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.NumberFilter(
        method='is_favorited_filter'
    )
    is_in_shopping_cart = filters.NumberFilter(
        method='is_in_shopping_cart_filter'
    )
    author = filters.CharFilter(field_name='author_id')
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),

    )

    def is_favorited_filter(self, queryset, name, value):
        user = self.request.user
        if not value or user.is_anonymous:
            return queryset
        return queryset.filter(favorite__user=user)

    def is_in_shopping_cart_filter(self, queryset, name, value):
        user = self.request.user
        if not value or user.is_anonymous:
            return queryset
        return queryset.filter(shopping_cart__user=user)

    class Meta:
        model = Recipe
        fields = (
            'is_favorited',
            'is_in_shopping_cart',
            'author',
            'tags'
        )


class IngredientFilter(filters.FilterSet):

    class Meta:
        model = Ingredient
        fields = {
            'name': ['startswith'],
        }
