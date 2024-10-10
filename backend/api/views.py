import short_url
from django.urls import reverse
from django.http import HttpResponseRedirect


def redirection(request, surl):
    id = short_url.decode_url(surl)
    return HttpResponseRedirect(
        reverse('api:recipes-detail', kwargs={'pk': id})
    )
