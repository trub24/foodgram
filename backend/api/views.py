import short_url
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from recipe.models import Recipe


def redirection(request, surl):
    id = short_url.decode_url(surl)
    recipe = get_object_or_404(Recipe, id=id)
    return redirect(recipe)
