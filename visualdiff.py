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

import base64
import urllib
from io import BytesIO, StringIO
from PIL import Image, ImageDraw
from math import floor
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

    def generateImages(self):
        before = urllib.request.urlopen(self.cleaned_data['before'])
        after = urllib.request.urlopen(self.cleaned_data['after'])

        before = BytesIO(before.read())
        after = BytesIO(after.read())

        before = Image.open(before)
        after = Image.open(after)

        # calc maximum common side size to resize
        before_size = list(before.size)
        after_size = list(after.size)

        if after.size[0] > before.size[0] and after.size[1] > before.size[1]:
            w_diff = after.size[0] - before.size[0]
            h_diff = after.size[1] - before.size[1]
            if (w_diff < h_diff):
                after_size[0], after_size[1] = after.size[0] - w_diff, after.size[1] - floor(w_diff / after.size[0] * after.size[1])
            else:
                after_size[0], after_size[1] = after.size[0] - floor(h_diff / after_size[1] * after.size[0]), after.size[1] - h_diff
        elif before.size[0] > after.size[0] and before.size[1] > after.size[1]:
            w_diff = before.size[0] - after.size[0]
            h_diff = before.size[1] - after.size[1]
            if (w_diff < h_diff):
                before_size[0], before_size[1] = before.size[0] - w_diff, before.size[1] - floor(w_diff / before.size[0] * before.size[1])
            else:
                before_size[0], before_size[1] = before.size[0] - floor(h_diff / before_size[1] * before.size[0]), before.size[1] - h_diff

        # calc overflows after resize
        before_crop = [0, 0, before_size[0], before_size[1]]
        after_crop = [0, 0, after_size[0], after_size[1]]

        # calc width to crop
        if after_size[0] > before_size[0]:
            diff = floor((after_size[0] - before_size[0]) / 2)
            after_crop[0], after_crop[2] = diff, after_size[0] - diff
        elif before_size[0] > after_size[0]:
            diff = floor((before_size[0] - after_size[0]) / 2)
            before_crop[0], before_crop[2] = diff, before_size[0] - diff

        # calc height to crop
        if after_size[1] > before_size[1]:
            diff = floor((after_size[1] - before_size[1]) / 2)
            after_crop[1], after_crop[3] = diff, after_size[1] - diff
        elif before_size[1] > after_size[1]:
            diff = floor((before_size[1] - after_size[1]) / 2)
            before_crop[1], before_crop[3] = diff, before_temp.size[1] - diff

        # do resize and crop
        before_resized = before.resize(before_size, Image.BILINEAR)
        before_cropped = before_resized.crop(before_crop)
        after_resized = after.resize(after_size, Image.BILINEAR)
        after_cropped = after_resized.crop(after_crop)

        before_content = BytesIO()
        before_cropped.save(before_content, before.format)
        before = 'data:image/{};base64,{}'.format(before.format, base64.b64encode(before_content.getvalue()).decode())

        after_content = BytesIO()
        after_cropped.save(after_content, after.format)
        after = 'data:image/{};base64,{}'.format(after.format, base64.b64encode(after_content.getvalue()).decode())

        return before, after

def generate_etag(request):
    before = request.GET.get('before')
    after = request.GET.get('after')
    content = 'Diff: {} x {}'.format(before, after)
    return hashlib.sha1(content.encode('utf-8')).hexdigest()

@etag(generate_etag)
def index(request):
    before = request.GET.get('before')
    after = request.GET.get('after')
    form = ImageForm({'before': before, 'after': after})
    if form.is_valid():
        before, after = form.generateImages()
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
