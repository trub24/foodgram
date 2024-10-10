import short_url
from django.shortcuts import redirect


def redirection(request, query):
    url = 'http://{}/{}'.format(
        'foodgram-12.zapto.org/recipes',
        short_url.decode(query)
    )
    return redirect(url)
