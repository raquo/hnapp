# -*- coding: utf-8 -*-
import urllib


# -----------------------------
# RENAME THIS FILE TO config.py
# -----------------------------


# Flask debug mode. Always set False on production
DEBUG = True


# Disable Flask's swallowing of unhandled exceptions
PROPAGATE_EXCEPTIONS = True


# URL where the app is hosted e.g. http://hnapp.com (without trailing slash)
HOST_NAME = ''


# Google Analytics ID (UA-XXXXXXXX-X). Set to None to disable tracking
GA_ID = None


# Number of items per page to show in GUI and RSS / JSON feeds
ITEMS_PER_PAGE = 30;


# Database connection string in the format engine://db_user:db_password@db_server/db_name
# Documentation: http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html
SQLALCHEMY_DATABASE_URI = 'engine://db_user:%s@db_server/db_name' % urllib.quote_plus('password')


