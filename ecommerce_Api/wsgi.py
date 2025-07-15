#import os
#from django.core.wsgi import get_wsgi_application
#os.environ.setdefault('DJANGO_SETTINGS_MODULE','ecommerce_Api.settings')
#application = get_wsgi_application()

import os
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler
from static_ranges import Ranges
from dj_static import Cling, MediaCling

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_Api.settings')

# Call get_wsgi_application just once
_base_application = get_wsgi_application()

if settings.DEBUG:
    application = StaticFilesHandler(_base_application)
else:
    application = Ranges(Cling(MediaCling(_base_application)))