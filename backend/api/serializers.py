import base64
import short_url
from django.core.files.base import ContentFile
from rest_framework import serializers
from users.models import User
from recipe.models import (
    Follow,
    Tag,
    Ingredient,
    Recipe,
    IngredientAmount,
    Favorite,
    IsInShoppingCart
)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserListSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField(
        'get_image_url', read_only=True,
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'avatar',
        )

    def get_image_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class UserSerializer(UserListSerializer):
    is_subscribed = serializers.SerializerMethodField('get_is_subscribed')

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, following=obj).exists()

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError('Не валидный никнейм')
        return value


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


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
        try:
            tag = Tag.objects.get(id=data)
            return tag
        except Tag.DoesNotExist:
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
            return IsInShoppingCart.objects.filter(
                user=self.context['request'].user,
                recipe=obj
            ).exists()
        return False


class RecipeCreateSerializer(СommonRecipeSerializer):
    image = Base64ImageField()
    ingredients = IngredientInRecipeSerializer(many=True,)
    cooking_time = serializers.IntegerField()

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Количество не может быть меньше нуля'
            )
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.short_link = "http://{}/{}".format(
            'foodgram-12.zapto.org',
            short_url.encode(recipe.id)
        )
        recipe.save()
        recipe.tags.set(tags)
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(id=ingredient['id'])
            IngredientAmount.objects.create(
                recipe=recipe,
                ingredient=current_ingredient,
                amount=ingredient['amount']
            )
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
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(id=ingredient['id'])
            IngredientAmount.objects.create(
                recipe=instance,
                ingredient=current_ingredient,
                amount=ingredient['amount']
            )
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


class RecipeSerializer(СommonRecipeSerializer):
    image = serializers.SerializerMethodField('get_image_url')
    ingredients = IngredienInRecipeReadSerializer(
        source='ingredient_in_recipe',
        many=True
    )

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id',)
    name = serializers.ReadOnlyField(source='recipe.name',)
    image = serializers.SerializerMethodField(
        'get_image_url', source='recipe.image'
    )
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time',)

    class Meta:
        model = Favorite
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )

    def get_image_url(self, obj):
        if obj.recipe.image:
            return obj.recipe.image.url
        return None


class ShoppingCartSerializer(FavoriteSerializer):

    class Meta:
        model = IsInShoppingCart
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscriptionsRecipeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField('get_image_url',)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class SubscriptionsSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    email = serializers.ReadOnlyField(source='following.email')
    avatar = serializers.SerializerMethodField(
        'get_avatar_url', source='following.avatar')
    is_subscribed = serializers.SerializerMethodField('get_is_subscribed')
    recipes_count = serializers.SerializerMethodField('get_recipes_count')
    recipes = serializers.SerializerMethodField('get_recipe')

    class Meta:
        model = Follow
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'avatar',
            'is_subscribed',
            'recipes_count',
            'recipes',
        )

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user=obj.user, following=obj.following
        ).exists()

    def get_recipes_count(self, obj):
        recipes = Recipe.objects.filter(author=obj.following)
        num = recipes.count()
        return num

    def get_recipe(self, obj):
        limit = self.context['request'].GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.following)
        if limit:
            recipes = recipes[:int(limit)]
        return SubscriptionsRecipeSerializer(
            recipes, read_only=True, many=True
        ).data

    def get_avatar_url(self, obj):
        if obj.following.avatar:
            return obj.following.avatar.url
        return None
