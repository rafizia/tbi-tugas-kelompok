# Import all settings from base
from .settings import *
import os

# Override critical settings
DEBUG = True  # Keep true for debugging
ALLOWED_HOSTS = ['*']  # Allow all hosts - Cloudflare provides security

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = '/app/staticfiles'

# Security settings for Cloudflare
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Disable CSRF for API endpoints temporarily
CSRF_COOKIE_SECURE = False
CSRF_USE_SESSIONS = False

# Override middleware to remove CSRF temporarily
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # Disabled temporarily
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

print('Production settings loaded successfully!')
