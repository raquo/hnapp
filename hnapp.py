# -*- coding: utf-8 -*-

import flask
import flask.ext.sqlalchemy
import sqlalchemy
import time
from werkzeug.contrib.atom import AtomFeed

# Initialize application and database session
app = flask.Flask(__name__,
	template_folder='templates',
	static_folder='static',
	static_url_path=''
	)
app.config.from_pyfile('config.py')
db = flask.ext.sqlalchemy.SQLAlchemy(app)

# Import hnapp components. These require app & db to be set
# <<< TODO is there a better way? Doesn't feel right...
from models.item import Item
from models.lost_item import LostItem
from models.status import Status
from search import Search
from utils import time_since, num_digits, query_url





@app.route('/rss', methods=['GET'])
@app.route('/json', methods=['GET'])
@app.route('/bare', methods=['GET'])
@app.route('/', methods=['GET'])
def route_search():
	
	# Get query
	text_query = flask.request.args.get('q', None)
	page_num = flask.request.args.get('page', 1);
	show_syntax = flask.request.args.get('show_syntax', 0)
	has_more_items = False
	expires = 0
	
	# Fail if bad parameters provided
	try:
		page_num = int(page_num)
		show_syntax = bool(int(show_syntax))
	except ValueError:
		flask.abort(400)
	
	# Search page 
	if text_query is not None:
		query = Search.query(text_query,
							 page_num,
							 offset=(page_num-1)*app.config['ITEMS_PER_PAGE'],
							 count=app.config['ITEMS_PER_PAGE']+1
							 )
		items = query.all()
		if len(items) == app.config['ITEMS_PER_PAGE']+1:
			items = items[:-1]
			has_more_items = True
		query_title = (text_query if len(text_query) > 0 else 'HN Firehose')
		meta_og_title = u'hnapp search: "%s"' % query_title
		title = u'%s – hnapp' % query_title
		
	# Front page
	else:
		query = None
		items = None
		title = u'hnapp – Hacker News RSS & JSON Feeds'
		meta_og_title = u'hnapp – Hacker News RSS'
	
	
	# Meta SEO tags
	meta_keywords = u'Hacker News,RSS,hnapp'
	meta_description = u'Follow users, keywords, jobs, mentions of your product, etc. Filter by score, domain, anything.'
	
	
	# Get format
	if flask.request.path == '/':
		output_format = None
		html_template = 'search.html'
	else:
		if text_query is None:
			flask.abort(400)
		output_format = flask.request.path[1:]
		if output_format == 'bare':
			html_template = 'parts/items.html'
	
	
	# Those users who created their filters on alpha version new.hnapp.com
	# don't expect comments, so we fix it for them
	if flask.request.args.get('legacy', 0) == '1':
		# Not a search – redirect to home page
		if text_query is None:
			return flask.redirect(query_url(None, output_format=None), code=302)
		else:
			return flask.redirect(query_url('type:story '+text_query, output_format=output_format), code=302)
	
	
	# Web page or bare HTML
	if output_format in (None, 'bare'):
		page_data = {
			'is_app': True,
			'title': title,
			'meta_og_title': meta_og_title,
			'meta_keywords': meta_keywords,
			'meta_description': meta_description,
			'show_syntax': show_syntax,
			'query': text_query,
			'items': items,
			'has_more_items': int(has_more_items),
			'page_expires_at': int(time.time()) + 60*5, # Cache pages for this many seconds
			'this_url': flask.request.url,
			'prev_url': query_url(text_query, page_num=page_num-1) if query is not None else None,
			'next_url': query_url(text_query, page_num=page_num+1) if query is not None else None,
			'rss_url': query_url(text_query, output_format='rss') if query is not None else None,
			'json_url': query_url(text_query, output_format='json') if query is not None else None,
			'page_num': page_num,
			'ga_id': app.config['GA_ID'],
			'HOST_NAME': app.config['HOST_NAME']
			}
		return flask.render_template(html_template, **page_data)
	
	
	# RSS
	elif output_format == 'rss':
		feed = AtomFeed(title=title.encode('ascii', 'xmlcharrefreplace'),
						title_type='html',
						feed_url=query_url(text_query, output_format='rss'),
						author='via hnapp',
						url=query_url(text_query),
						generator=('hnapp', app.config['HOST_NAME'], None)
						)
		for item in items:
			feed.add(**item.feed_entry())
		return feed.get_response()
		
	
	# JSON
	elif output_format == 'json':
		
		feed = {}
		feed['has_more_items'] = has_more_items
		feed['query'] = text_query
		feed['items'] = [item.json_entry() for item in items]
		return flask.jsonify(**feed)
	
	
	# output_format defined but query is not
	# not supposed to happen, we checked for this above
	else:
		flask.abort(500)



@app.route('/status', methods=['GET'])
def route_status():
	
	statuses = db.session.query(Status).all()
	max_item_id = db.engine.execute(sqlalchemy.sql.text('SELECT MAX(id) FROM item')).scalar()
	min_item_id = db.engine.execute(sqlalchemy.sql.text('SELECT MIN(id) FROM item')).scalar()
	item_count  = db.engine.execute(sqlalchemy.sql.text('SELECT COUNT(*) FROM item')).scalar()
	lost_item_ids = db.session.query(LostItem.id).all() # db.engine.execute(sqlalchemy.sql.text('SELECT id FROM lost_item ORDER BY id DESC')).scalar()
	page_data = {
		'is_app': False,
		'title': u'hnapp – Status',
		'meta_og_title': u'hnapp – Status',
		'statuses': statuses,
		'max_item_id': max_item_id,
		'min_item_id': min_item_id,
		'item_count': item_count,
		'lost_item_ids': ', '.join([str(item[0]) for item in lost_item_ids]),
		'ga_id': app.config['GA_ID'],
		'HOST_NAME': app.config['HOST_NAME']
		}
	return flask.render_template('status.html', **page_data)



@app.errorhandler(400)
def error(e):
	return flask.render_template('error.html',
								 is_app=False,
								 error=u'400 – Bad Request',
								 ga_id=app.config['GA_ID']
								 ), 400



@app.errorhandler(404)
def error(e):
	return flask.render_template('error.html',
								 is_app=False,
								 error=u'404 – Page Not Found',
								 ga_id=app.config['GA_ID']
								 ), 404



@app.errorhandler(403)
def error(e):
	return flask.render_template('error.html',
								 is_app=False,
								 error=u'403 – Access Denied',
								 ga_id=app.config['GA_ID']
								 ), 403



@app.errorhandler(500)
def error(e):
	return flask.render_template('error.html',
								 is_app=False,
								 error=u'500 – Internal Server Error',
								 ga_id=app.config['GA_ID']
								 ), 500



