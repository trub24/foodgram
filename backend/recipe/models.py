from django.db import models
from users.models import User


class Tag(models.Model):
    name = models.CharField('название', max_length=32,)
    slug = models.SlugField('слаг', max_length=32, unique=True)

    class Meta:
        default_related_name = 'tag'
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('название', max_length=128,)
    measurement_unit = models.CharField('единицы измерения', max_length=64,)

    class Meta:
        default_related_name = 'Ingredient'
        verbose_name = 'ингридиент'
        verbose_name_plural = 'Интгридиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag, verbose_name='Тэг',)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientAmount',
        verbose_name='ингридиенты',
    )
    name = models.CharField('название', max_length=256,)
    image = models.ImageField('Картинака', upload_to='recipe/images/',)
    text = models.TextField('описание',)
    cooking_time = models.PositiveIntegerField('время приготовления',)
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    short_link = models.CharField(
        'Короткая ссылка',
        max_length=256,
        unique=True
    )

    class Meta:
        default_related_name = 'recipe'
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', )

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингридиент'
    )
    amount = models.PositiveIntegerField(
        'Необходимое количестово',
        default=1,
    )

    class Meta:
        default_related_name = 'ingredient_in_recipe'
        verbose_name = 'ингридиент в рецепте'
        verbose_name_plural = 'Ингридиент в рецепте'

    def __str__(self):
        return f'{self.ingredient} {self.amount}'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follow',
        verbose_name='Юзер',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписки',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_subs'
            )
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} {self.following}'


class IsInShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='юзер',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='рецепт',
    )

    class Meta():
        default_related_name = 'shopping_cart'
        verbose_name = 'корзина'
        verbose_name_plural = 'Корзина'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='юзер',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='рецепт',
    )

    class Meta():
        default_related_name = 'favorite'
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'
