
from hnapp import app

import urllib
from datetime import datetime
from math import log10




def debug_print(*items):
	"""Print only if DEBUG is True in config.py"""
	
	if items and app.config['DEBUG']:
		print ' '.join([str(item) for item in items])



def query_url(text_query, page_num=1, output_format=None):
	"""Compile URL given a query and output format"""
	
	url = app.config['HOST_NAME']+'/'
	if output_format is not None:
		url += output_format
	if text_query is not None:
		url += '?q=' + urllib.quote(text_query.encode('utf8'))
		if page_num != 1:
			url += '&page=%d' % page_num
	return url



@app.template_filter()
def time_since(dt, default="just now"):
	"""
	Returns string representing "time since" e.g. 3 days ago, 5 hours ago, etc.
	source: http://flask.pocoo.org/snippets/33/
	"""
	
	now = datetime.utcnow()
	diff = now - dt
	
	periods = (
		(diff.days / 365, "year", "years"),
		(diff.days / 30, "month", "months"),
		(diff.days / 7, "week", "weeks"),
		(diff.days, "day", "days"),
		(diff.seconds / 3600, "hour", "hours"),
		(diff.seconds / 60, "minute", "minutes"),
		(diff.seconds, "second", "seconds"),
	)

	for period, singular, plural in periods:
		if period:
			return "%d %s ago" % (period, singular if period == 1 else plural)

	return default



@app.template_filter()
def num_digits(score, default=0):
	return 1 + int(log10(score))






