# -*- coding: utf-8 -*-

import requests
import json
import traceback

from firebase import firebase
from urlparse import urlparse, urljoin
from datetime import datetime
import sqlalchemy
import bleach

from hnapp import app, db
from models.item import Item
from models.lost_item import LostItem
from models.status import Status
from utils import debug_print
from errors import AppError, ScraperError




class Scraper(object):
	
	firebase = None
	base_url = 'https://hacker-news.firebaseio.com/v0/'
	
	
	def connect(self):
		"""
		Connect to firebase API
		You must call this before using the API
		<<< TODO: call this from constructor
		"""
		if not self.firebase:
			self.firebase = firebase.FirebaseApplication(self.base_url, None)
	
	
	
	
	def save_newest_items(self):
		"""
		Get list of item dicts from the newest items by id
		Includes all acceptable kinds of items (ignores pollopts)
		Saves items in order of ascending ID – important for parent_id and root_id references
		"""
		
		# Get latest item ids from db and from api
		max_api_id = self.fetch_max_item_id()
		max_db_id = Status.get_max_item_id()
		
		# If no new data, quit. We don't want to use this function to update items
		if (max_api_id <= max_db_id):
			return
		
		# Save latest items and update max id
		save = lambda item_data: self.save_item(item_data, update_max_id=True)
		self.fetch_items(range(max_db_id+1, max_api_id), callback=save)
		
	
	
	
	def save_newest_existing_stories(self, start_from=0, count=100, min_delay=0):
		"""
		Save latest stories
		Does not fetch new stories, uses only those available in database
		Basically this updates story scores
		"""
		
		# Generate list of newest stories
		# <<< TODO: Actually, we only need ids
		stories = (db.session.query(Item)
							 .with_entities(Item.id)
							 .filter(Item.kind == 'story')
							 .filter(Item.deleted == 0, Item.dead == 0)
							 .order_by(sqlalchemy.desc(Item.id))
							 .slice(start_from, count+start_from)
							 .all()
							 )
		
		save = lambda item_data: self.save_item(item_data)
		self.fetch_items([item.id for item in stories], callback=save, min_delay=min_delay)
		
	
	
	
	def save_top_stories(self, front_page, start_from=0, count=100, min_delay=0):
		"""
		Save top stories (ranked by front page order)
		Must indicate whether we're loading front page or not
		"""
		
		# Generate list of top stories
		story_ids = self.fetch_top_story_ids()[start_from:start_from+count]
		
		# Save top stories
		save = lambda item_data: self.save_item(item_data, front_page=front_page)
		# def save_item = function(item):
		# 	if (datetime.utcnow() - item.date_updated).total_seconds() > min_delay:
		# 		self.save_item(item_data)
		stories = self.fetch_items(story_ids, callback=save, min_delay=min_delay)
		
	
	
	
	def save_item(self, item_data, update_max_id=False, front_page=False):
		"""
		Compile and save item to the database
		Each item is committed separately for better fault tolerance
		"""
		
		# If item was lost
		if isinstance(item_data, LostItem):
			db.session.add(item_data)
			debug_print("Lost %s because %s" % (item_data.id, item_data.reason), '\n')
		else:
			if item_data.get('type', None) in ('story', 'comment', 'poll', 'job', None):
				debug_print("Saving %d" % item_data['id'], '\n')
				compiled_data = self.compile_item_data(item_data, front_page)
				item = Item.create_or_update(compiled_data)
			else:
				debug_print("Skipping %s %d" % (item_data['type'], item_data['id']), '\n')
		
		if update_max_id:
			Status.set_max_item_id(item_data.id if isinstance(item_data, LostItem) else item_data['id'])
		
		db.session.commit()
		
		return item
		
	
	
	
	def bleach_html(self, html):
		"""
		Sanitize HTML. Leave only safe/expected markup
		"""
		
		return bleach.clean(
			'<p>' + html.replace('<p>', '</p>\n\n<p>') + '</p>',
			tags=('a', 'i', 'p', 'pre'),
			attributes={'a': ['href']},
			styles=(),
			strip=True
			).replace('<p></p>', '')
	
	
	
	def compile_item_data(self, raw_item, front_page):
		"""
		Convert raw API output for item to a source dict for an Item model
		"""
		
		# fields map {api_field: hnapp_field}
		fields = {
			'id': 'id',
			'parent': 'parent_id',
			'type': 'kind',
			'title': 'title',
			'text': 'raw_body',
			'by': 'author',
			'score': 'score',
			'dead': 'dead',
			'deleted': 'deleted'
		}
		
		item_data = {}
		
		# Set standard fields listed above
		for raw_field, model_field in fields.iteritems():
			if raw_field in raw_item:
				item_data[model_field] = raw_item[raw_field]
		
		# Set time
		if 'time' in raw_item:
			item_data['date_posted'] = datetime.fromtimestamp(raw_item['time'])
		
		# Set sanitized body
		if 'text' in raw_item:
			item_data['body'] = self.bleach_html(raw_item['text'])
		
		# Set (or unset) URL and domain
		if raw_item.get('url', None) is not None:
			if len(raw_item['url']) == 0:
				item_data['url'] = None
				item_data['domain'] = None
			else:
				parsed_url = urlparse(raw_item['url'])
				item_data['domain'] = parsed_url.hostname.lower()
				item_data['url'] = raw_item['url'] # <<< should we use urlunparse here? https://docs.python.org/2/library/urlparse.html#urlparse.urlunparse
				if item_data['domain'][:4] == 'www.':
					item_data['domain'] = item_data['domain'][4:]
		
		# Detect broken stories
		if raw_item.get('type', None) != 'comment' and 'title' not in raw_item:
			item_data['deleted'] = True
		
		# Set kind and subkind
		# item types map {api_type: [hnapp_kind, hnapp_subkind]}
		item_types = {
			'comment': ['comment', 'comment'],
			'story': ['story', 'link'],
			'poll': ['story', 'poll'],
			'job': ['story', 'job'],
			None: ['story', 'link'] # <<< broken item... maybe these fields should be nullable in DB
		}
		item_data['kind'], item_data['subkind'] = item_types[raw_item.get('type', None)]
		# Special treatment for ask/show stories
		if item_data['subkind'] == 'link' and not item_data.get('deleted', False):
			if 'text' in raw_item and item_data.get('domain', None) is None:
				# Semi-killed items like 8549613 can have no URL, but also don't have a text field
				# Non-broken items on the other hand do have the text field, empty of unapplicable
				item_data['subkind'] = 'ask'
			if item_data['title'].lower()[0:8] == 'show hn:':
				item_data['subkind'] = 'show'
		
		# Set child ids
		if 'kids' in raw_item:
			item_data['child_ids'] = ','.join(str(child_id) for child_id in raw_item['kids'])
		
		# Set date when item entered and left front page
		if front_page:
			item_data['date_entered_fp'] = datetime.utcnow()
		
		# Restore non-deleted and non-dead status
		# Also cast those to int-s for postgresql
		if 'deleted' not in item_data:
			item_data['deleted'] = 0
		else:
			item_data['deleted'] = int(item_data['deleted'])
		if 'dead' not in item_data:
			item_data['dead'] = 0
		else:
			item_data['dead'] = int(item_data['dead'])
		
		return item_data
	
	
	
	
	def fetch_max_item_id(self):
		"""
		Fetch max item id available via HN Firebase API
		"""
		debug_print(">> fetch_max_item_id")
		max_id = self.firebase.get('maxitem', None)
		debug_print(max_id, '\n')
		
		return max_id
	
	
	
	
	def fetch_item(self, item_id):
		"""
		Fetch item data by id
		Might return an instance of LostItem in case of API or HTTP error
		"""
		debug_print(">> fetch_item %d" % item_id)
		
		try:
			item = self.firebase.get('item', item_id)
			if item is None:
				item = LostItem(id=item_id,
								reason='null'
								)
			return item
		except requests.exceptions.HTTPError as e:
			# If API error encountered, return a LostItem instead
			lost_item = db.session.query(LostItem).get(item_id)
			if lost_item is None:
				lost_item = LostItem(id=item_id,
									 reason='HTTP/%s' % e.response.status_code,
									 response=e.response.text,
									 traceback=traceback.format_exc()
									 )
			return lost_item
	
	
	
	
	def fetch_items(self, item_ids, callback=None, min_delay=0):
		"""
		Fetch items for item ids
		Output format: {id1: {item1}, id2: {item2}, ...}
		
		Failed items might appear as LostItem instances instead of attribute dictionaries
		"""
		debug_print(">> fetch_items")
		
		items = {}
		for item_id in item_ids:
			# Skip items that have been recently updated, if requested
			if min_delay > 0:
				db_item = db.session.query(Item).get(item_id)
				if db_item is not None and min_delay > (datetime.utcnow() - db_item.date_updated).total_seconds():
					debug_print("Skipped item %d because it's too fresh" % item_id)
					continue
			api_item = self.fetch_item(item_id)
			items[item_id] = api_item
			if callback is not None:
				callback(api_item)
		
		return items
	
	
	
	
	def fetch_top_story_ids(self):
		"""
		Fetch stories from top 100 items on front page
		Ordered by current front page rank
		"""
		debug_print(">> fetch_top_story_ids")
		
		return self.firebase.get('topstories', None)
	
	
	
	
	
	
	








