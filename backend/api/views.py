import short_url
from django.http import HttpResponseRedirect 
from django.urls import reverse

def redirection(request, surl):
    id = short_url.decode_url(surl)
    return HttpResponseRedirect(reversed(
        'api:recipes', kwargs={'recipe_id': id}
    ))
