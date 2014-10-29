# -*- coding: utf-8 -*-

import flask
import flask.ext.sqlalchemy
# import PyRSS2Gen
# from feedgen.feed import FeedGenerator
# from datetime import datetime
from werkzeug.contrib.atom import AtomFeed
# from utils import UTC
import urllib

# import sqlalchemy
# from sqlalchemy import func

app = flask.Flask(__name__,
	template_folder='templates',
	static_folder='static',
	static_url_path=''
	)
app.config.from_pyfile('config.py')

db = flask.ext.sqlalchemy.SQLAlchemy(app)

from models.item import Item
from search import Search

from urlparse import urljoin
from datetime import datetime

@app.template_filter()
def domain(item):
	if item.domain is None:
		return 'self.%s' % item.subkind
	return item.domain


@app.template_filter()
def timesince(dt, default="just now"):
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

@app.before_request
def remove_trailing_slash():
	if flask.request.path != '/' and flask.request.path.endswith('/'):
		return flask.redirect(flask.request.path[:-1])



@app.errorhandler(404)
def error_404(e):
	return flask.render_template('error_404.html'), 404


def query_url(text_query, output_format=None):
	url = app.config['HOST_NAME']+'/'
	if output_format is not None:
		url += output_format
	if text_query is not None:
		url += '?q=' + urllib.quote(text_query.encode('utf8'))
	return url


@app.route('/rss', methods=['GET'])
@app.route('/json', methods=['GET'])
@app.route('/', methods=['GET'])
def route_rss():
	
	# Get query and format
	text_query = flask.request.args.get('q', None)
	url_rule = flask.request.url_rule
	output_format = flask.request.args.get('format', None)
	
	print flask.request.path
	
	# Parse query if it is set
	if text_query is not None:
		query = Search.query(text_query)
		items = query.all()
	else:
		query = None
		items = None
	
	# Web page
	if flask.request.path == '/':
		page_data = {
			'title': u'hnapp – Filter Hacker News. Get via web, RSS or JSON',
			'query': text_query,
			'items': items,
			'rss_url': query_url(text_query, output_format='rss'), # flask.request.url + '&format=rss', # <<< !!!
			'json_url': query_url(text_query, output_format='json') #flask.request.url + '&format=rss' # <<< !!!
			}
		return flask.render_template('home.html', **page_data)
	
	# RSS
	elif flask.request.path == '/rss' and query is not None:
		feed = AtomFeed(title=(u'hnapp: %s' % (text_query if text_query != '' else 'all')).encode('ascii', 'xmlcharrefreplace'),
						title_type='text',
						feed_url=query_url(text_query, output_format='rss'),
						author='via hnapp',
						# feed_url=flask.request.url,
						url=query_url(text_query),
						# url = flask.request.url,
						generator=('hnapp', app.config['HOST_NAME'], None)
						)
		for item in items:
			feed.add(**item.feed_entry())
		return feed.get_response()
		
	
	# JSON
	elif flask.request.path == '/json' and query is not None:
		
		feed = {}
		feed['query'] = text_query
		feed['items'] = [item.json_entry() for item in items]
		return flask.jsonify(**feed)
	
	# output_format defined but query is not
	else:
		flask.abort(404)
	
	# Compile RSS feed
	# feed = FeedGenerator()
	# feed.title('hnapp: %s' % text_query)
	# feed.description('hnapp: %s' % text_query)
	# feed.link(href=flask.request.url, rel='alternate') # <<< !!!
	# feed.language('en')
	# # Add items
	# for item in items:
	# 	entry = feed.add_entry()
	# 	entry.title(item.title)
	# 	entry.link(href=item.main_url(), rel='alternate')
	# 	entry.description(item.feed_description())
	# 	entry.guid(item.comments_url())
	# 	entry.published(published=item.date_posted.replace(tzinfo=UTC()))
	# return feed.rss_str(pretty=True)


@app.route('/test', methods=['GET'])
def route_test():
	
	return
	# page_data = {
	# 	'config': app.config,
	# 	'items': scraper.items,
	# 	'more_url': scraper.more_url
	# 	}
	# return flask.render_template('test.html', **page_data)



