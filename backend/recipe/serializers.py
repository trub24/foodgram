from rest_framework import serializers
from users.serializers import UserSerializer
from api.utils import Base64ImageField
from recipe.models import (
    Tag,
    Ingredient,
    Recipe,
    IngredientAmount,
    Favorite,
    ShoppingCart
)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class IngredienInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id',)
    name = serializers.ReadOnlyField(source='ingredient.name',)
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta():
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientInRecipeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(write_only=True)

    def validate_id(self, value):
        if Ingredient.objects.filter(id=value).exists():
            return value
        raise serializers.ValidationError('Ингидиент отсутствует')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Количество не может быть меньше нуля'
            )
        return value


class RecipeTagField(serializers.RelatedField):
    def to_representation(self, value):
        return TagSerializer(value).data

    def to_internal_value(self, data):
        tag = Tag.objects.filter(id=data).first()
        if tag:
            return tag
        raise serializers.ValidationError('Тэг отсутствует')

    def get_queryset(self):
        return self.queryset


class СommonRecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = RecipeTagField(many=True)
    ingredients = IngredienInRecipeReadSerializer(
        source='ingredient_in_recipe',
        many=True
    )
    is_favorited = serializers.SerializerMethodField(
        'get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        'get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        if self.context['request'].user.is_authenticated:
            return Favorite.objects.filter(
                user=self.context['request'].user,
                recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        if self.context['request'].user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=self.context['request'].user,
                recipe=obj
            ).exists()
        return False


class RecipeCreateSerializer(СommonRecipeSerializer):
    image = Base64ImageField()
    ingredients = IngredientInRecipeSerializer(many=True,)
    cooking_time = serializers.IntegerField(min_value=1, max_value=5000)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.short_link = 'https://{}/{}'.format(
            'foodgram-12.zapto.org/recipes',
            recipe.id
        )
        recipe.save()
        recipe.tags.set(tags)
        list_ing = [
            IngredientAmount(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ]
        IngredientAmount.objects.bulk_create(list_ing)
        return recipe

    def update(self, instance, validated_data):
        if validated_data.get(
            'ingredients'
        ) is None or validated_data.get(
            'tags'
        ) is None:
            raise serializers.ValidationError('Не заполнены обязательные поля')
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.ingredients.clear()
        instance.tags.set(tags)
        list_ing = [
            IngredientAmount(
                recipe=instance,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ]
        IngredientAmount.objects.bulk_create(list_ing)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        value_data = super().to_representation(instance)
        value_data['ingredients'] = IngredienInRecipeReadSerializer(
            instance.ingredient_in_recipe.all(), many=True
        ).data
        return value_data

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать Тег(и).'
            )
        list_value = []
        for tag in value:
            if tag in list_value:
                raise serializers.ValidationError('Тэги не должны повторяться')
            list_value.append(tag)
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать Ингридиент(ы).'
            )
        list_value = []
        for ingredient in value:
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise serializers.ValidationError(
                    'Выберите существующие ингридиенты'
                )
            if ingredient in list_value:
                raise serializers.ValidationError(
                    'Ингридиенты не должны повторяться'
                )
            list_value.append(ingredient)
        return value


class RecipeReadSerializer(СommonRecipeSerializer):
    image = serializers.SerializerMethodField('get_image_url')
    ingredients = IngredienInRecipeReadSerializer(
        source='ingredient_in_recipe',
        many=True
    )

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class FavoriteShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id',)
    name = serializers.ReadOnlyField(source='recipe.name',)
    image = serializers.SerializerMethodField(
        'get_image_url', source='recipe.image'
    )
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time',)

    def get_image_url(self, obj):
        if obj.recipe.image:
            return obj.recipe.image.url
        return None


class FavoriteSerializer(FavoriteShoppingCartSerializer):

    class Meta:
        model = Favorite
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class ShoppingCartSerializer(FavoriteShoppingCartSerializer):

    class Meta:
        model = ShoppingCart
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
