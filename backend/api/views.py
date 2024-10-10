import short_url
from django.http import HttpResponseRedirect


def redirection(request, surl):
    redirect_url = 'https://{}/{}/{}'.format(
        'foodgram-12.zapto.org',
        'recipes',
        short_url.decode_url(surl)
    )
    return HttpResponseRedirect(redirect_url)
