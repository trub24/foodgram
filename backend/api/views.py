import short_url
from django.shortcuts import redirect


def redirection(request, surl):
    id = short_url.decode_url(surl)
    return redirect('api:recipes', kwargs={'recipe_id': id})
