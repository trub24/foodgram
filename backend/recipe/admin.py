from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from users.models import User
from recipe.models import (
    Tag,
    Ingredient,
    Recipe,
    IngredientAmount,
    Follow,
    IsInShoppingCart,
    Favorite
)


class IngredientResource(resources.ModelResource):

    class Meta:
        model = Ingredient


class IngredientAdmin(ImportExportModelAdmin):
    resource_classes = [IngredientResource]


admin.site.unregister(Group)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe)
admin.site.register(IngredientAmount)
admin.site.register(Follow)
admin.site.register(IsInShoppingCart)
admin.site.register(Favorite)


UserAdmin.fieldsets += (
    ('Extra Fields', {'fields': ('avatar',)}),
)

admin.site.register(User, UserAdmin)
