# Django settings for cidec_sw project.
#import djcelery
#djcelery.setup_loader()
import os
BROKER_HOST = "myhost"
BROKER_PORT = "5672"
BROKER_USER = "cidec_user"
BROKER_PASSWORD = "a8d32e08"
BROKER_VHOST = 'cidec_vhost'

PROJECT_PATH = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.path.pardir))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

"""DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'audiwime_db',                      # Or path to database file if using sqlite3.
        'USER': 'audiwime_user',                      # Not used with sqlite3.
        'PASSWORD': 'A8d32e08.',#'5MnT)HXnm_pT',                  # Not used with sqlite3.
        'HOST': 'audiwime.wimelabs.com',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}"""
"""DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'satest_cidec',                      # Or path to database file if using sqlite3.
        'USER': 'satest_cidec',                      # Not used with sqlite3.
        'PASSWORD': '5MnT)HXnm_pT',                  # Not used with sqlite3.
        'HOST': 'auditem.mx',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with
        # sqlite3.
    }
}"""
DATABASES = {
'default': {
    'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
    'NAME': 'audiwime_db',                      # Or path to database file if using sqlite3.
    'USER': 'root',                      # Not used with sqlite3.
    'PASSWORD': '',                  # Not used with sqlite3.
    'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
    'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
}
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Mexico_City'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'templates/static/media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/static/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
#STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, 'templates/static/'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'tr&amp;!=v*6v--y&amp;8bg20v4+%m3u9aj6ekbv-(ei$jst90h9tdz_c'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'cidec_sw.middleware.timezones.TimezoneMiddleware'
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'cidec_sw.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'cidec_sw.wsgi.application'

TEMPLATE_DIRS = (os.path.join(PROJECT_PATH, 'templates'))#'/Users/wime/Dev/wime_dev/cidec_sw/templates',)

INSTALLED_APPS = (
    'grappelli',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    #'django.contrib.admindocs',
    'location',
    'c_center',
    'rbac',
    'electric_rates',
    'south',
    'data_warehouse',
    #'djcelery',
    'tareas',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

GRAPPELLI_ADMIN_TITLE = 'CIDEC'