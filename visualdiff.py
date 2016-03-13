import hashlib
import os
import sys

from django.conf import settings

DEBUG = os.environ.get('DEBUG', 'on') == 'on'

SECRET_KEY = os.environ.get('SECRET_KEY', 'oaz5jeh3v%&ex3*xtk2-d+kifvb-8y(fp#aywla2v=b@zdo(tz')

BASE_DIR = os.path.dirname(__file__)

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

settings.configure(
    DEBUG=DEBUG,
    SECRET_KEY=SECRET_KEY,
    ROOT_URLCONF=__name__,
    MIDDLEWARE_CLASSES=(
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ),
    INSTALLED_APPS=(
        'django.contrib.staticfiles',
    ),
    TEMPLATES=(
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': (os.path.join(BASE_DIR, 'templates'), ),
        },
    ),
    STATICFILES_DIRS=(
        os.path.join(BASE_DIR, 'static'),
    ),
    STATIC_URL='/static/',
)

from django import forms
from django.conf.urls import url
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import etag

class ImageForm(forms.Form):
    """Form to validate requested diff."""

    before = forms.URLField(required=True)
    after = forms.URLField(required=True)

def generate_etag(request):
    before = request.GET.get('before')
    after = request.GET.get('after')
    content = 'Diff: {0} x {1}'.format(before, after)
    return hashlib.sha1(content.encode('utf-8')).hexdigest()

@etag(generate_etag)
def index(request):
    before = request.GET.get('before')
    after = request.GET.get('after')
    form = ImageForm({'before': before, 'after': after})
    if form.is_valid():
        context = {
            'before': before,
            'after': after
        }
    else:
        example = reverse('homepage')
        context = {
            'usage': True,
            'example': request.build_absolute_uri(example)
        }
    return render(request, 'home.html', context)

urlpatterns = (
    url(r'^$', index, name='homepage'),
)

application = get_wsgi_application()

if __name__=="__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
