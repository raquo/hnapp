# -*- coding: utf-8 -*-
import urllib


# -----------------------------
# RENAME THIS FILE TO config.py
# -----------------------------


# Flask debug mode. Always set False on production
DEBUG = True


# URL where the app is hosted e.g. http://hnapp.com (without trailing slash)
# <<< eh... SERVER_NAME?
HOST_NAME = ''


# Database connection string in the format engine://db_user:db_password@db_server/db_name
# Documentation: http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html
SQLALCHEMY_DATABASE_URI = 'engine://db_user:%s@db_server/db_name' % urllib.quote_plus('password')


