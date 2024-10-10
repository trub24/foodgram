import short_url
from django.shortcuts import redirect


def redirection(request, query):
    id = short_url.decode(query)
    return redirect(f'https://foodgram-12.zapto.org/recipes/{id}')
