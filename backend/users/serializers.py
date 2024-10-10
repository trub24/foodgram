from rest_framework import serializers
from django.contrib.auth import get_user_model
from recipe.models import Follow, Recipe
from api.utils import Base64ImageField


User = get_user_model()


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
