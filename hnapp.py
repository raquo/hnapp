# -*- coding: utf-8 -*-

import flask
import flask.ext.sqlalchemy
import sqlalchemy

from werkzeug.contrib.atom import AtomFeed
import urllib

app = flask.Flask(__name__,
	template_folder='templates',
	static_folder='static',
	static_url_path=''
	)
app.config.from_pyfile('config.py')

db = flask.ext.sqlalchemy.SQLAlchemy(app)

from models.item import Item
from models.lost_item import LostItem
from models.status import Status
from search import Search

from urlparse import urljoin
from datetime import datetime




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
	
	# <<< Shall we split this into three routes?
	
	# Get query and format
	text_query = flask.request.args.get('q', None)
	url_rule = flask.request.url_rule
	output_format = flask.request.args.get('format', None)
	
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



@app.route('/status', methods=['GET'])
def route_status():
	statuses = db.session.query(Status).all()
	max_item_id = db.engine.execute(sqlalchemy.sql.text('SELECT MAX(id) FROM item')).scalar()
	min_item_id = db.engine.execute(sqlalchemy.sql.text('SELECT MIN(id) FROM item')).scalar()
	item_count  = db.engine.execute(sqlalchemy.sql.text('SELECT COUNT(*) FROM item')).scalar()
	lost_item_ids = db.session.query(LostItem.id).all() # db.engine.execute(sqlalchemy.sql.text('SELECT id FROM lost_item ORDER BY id DESC')).scalar()
	page_data = {
		'title': u'hnapp – Status',
		'statuses': statuses,
		'max_item_id': max_item_id,
		'min_item_id': min_item_id,
		'item_count': item_count,
		'lost_item_ids': ', '.join([str(item[0]) for item in lost_item_ids])
		}
	return flask.render_template('status.html', **page_data)



@app.errorhandler(404)
def error(e):
	return flask.render_template('error.html', error=u'404 – Page Not Found'), 404



@app.errorhandler(403)
def error(e):
	return flask.render_template('error.html', error=u'403 – Access Denied'), 403



@app.errorhandler(500)
def error(e):
	return flask.render_template('error.html', error=u'500 – Internal Server Error'), 500



