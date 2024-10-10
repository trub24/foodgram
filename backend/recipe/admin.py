from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from users.models import User
from recipe.models import (
    Tag,
    Ingredient,
    Recipe,
    IngredientAmount,
    Follow,
    ShoppingCart,
    Favorite
)


class IngredientResource(resources.ModelResource):

    class Meta:
        model = Ingredient


class IngredientAdmin(ImportExportModelAdmin):
    resource_classes = [IngredientResource]
    search_fields = ['name', ]


admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe)
admin.site.register(IngredientAmount)
admin.site.register(Follow)
admin.site.register(ShoppingCart)
admin.site.register(Favorite)


UserAdmin.fieldsets += (
    ('Extra Fields', {'fields': ('avatar',)}),
)

admin.site.register(User, UserAdmin)
