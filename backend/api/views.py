import short_url
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from recipe.models import Recipe


def redirection(request, surl):
    url = 'https://{}/{}/{}'.format(
        'foodgram-12.zapto.org',
        'recipes',
        short_url.decode_url(surl)
    )
    return redirect(url)
