# -*- coding: utf-8 -*-

import sqlalchemy
from sqlalchemy import Column, Integer, Numeric, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import INTEGER
# from sqlalchemy.dialects.postgresql import JSONElement
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import validates, relationship, backref
import sqlalchemy.ext.declarative

from datetime import datetime

from hnapp import db
from errors import AppError, ValidationError


class Item(sqlalchemy.ext.declarative.declarative_base()):
	
	__tablename__ = 'item'
	
	id = Column(Integer, primary_key=True)
	kind = Column(Enum('story', 'comment'), nullable=False, default=None) # pollopt is ignored
	subkind = Column(Enum('link', 'ask', 'show', 'poll', 'job', 'comment'), nullable=False, default=None)
	
	root_id = Column(Integer, ForeignKey('item.id'))
	root = relationship('Item', backref='root_descendants', foreign_keys=[root_id], remote_side=id)
	
	parent_id = Column(Integer, ForeignKey('item.id'))
	parent = relationship('Item', backref='children', foreign_keys=[parent_id], remote_side=id)
	
	title = Column(String, nullable=True, default=None)
	body = Column(Text, nullable=True, default=None)
	raw_body = Column(Text, nullable=True, default=None)
	url = Column(Text, nullable=True, default=None)
	
	author = Column(String, nullable=True, default=None)
	domain = Column(String, nullable=True, default=None)
	
	score = Column(Integer, nullable=True, default=None)
	num_comments = Column(Integer, default=0)
	
	# Comma-separated list of child ids
	# Currently not used, saving those in case we'll need comment ranking info later on
	child_ids = Column(Text)
	
	# Date fields
	date_posted = Column(DateTime, default=datetime.utcnow)
	date_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	date_entered_fp = Column(DateTime, default=None)
	date_left_fp = Column(DateTime, default=None)
	
	deleted = Column(Integer, default=0)
	dead = Column(Integer, default=0)
	
	# PostgreSQL search fields
	title_tsv = Column(TSVECTOR)
	body_tsv = Column(TSVECTOR)
	
	
	
	# def update
	
	
	
	
	@validates('dead', 'deleted')
	def validate_yesno(self, key, value):
		if value not in (0, 1):
			raise ValidationError('Bad value for key %s: %s' % (key, value))
		return value
	
	
	
	
	@classmethod
	def create(cls, data):
		"""
		Create a new item with data
		Update comment counts as needed
		"""
		
		item = Item(**data)
		db.session.add(item)
		# Flush session to get item's relationships to work (%%% Why is this needed?)
		# <<< I've enabled autoflush. I don't really need this anymore, right?
		db.session.flush()
		
		if item.kind == 'comment':
			# Find root and update root_id
			root = item.find_root()
			if root is not None:
				item.root_id = root.id
				# Update root's number of comments
				if not item.deleted:
					root.num_comments += 1
					# print "Added comments to %d: now %d" % (root.id, root.num_comments)
		else: # item.kind == 'story'				
			# Find and count story's existing comments
			num_comments = 0
			for comment in item.descendants():
				# Set story as comment's root
				comment.root_id = item.id
				# Update comment count only if comment is not deleted
				if not comment.deleted:
					num_comments += 1
			item.num_comments = num_comments
		
		return item
	
	
	
	def update(self, data):
		"""
		Update item with data
		Update comment counts as needed
		"""
		
		item_was_deleted = self.deleted
		item_had_root = self.root_id
		
		# Update date on which item was first detected on front page
		if 'date_entered_fp' in data and self.date_entered_fp is None:
			self.date_entered_fp = data['date_entered_fp']
		
		# Update all other fields
		for key, value in data.iteritems():
			if key in self.__class__.__table__.columns:
				if key not in ('id', 'date_entered_fp', 'date_left_fp'):
					setattr(self, key, value)
		
		if self.kind == 'comment':
			# Find and set root
			if self.root_id is None:
				root = self.find_root()
				if root is not None:
					self.root_id = root.id
			# If w're deleting an item, and it already had a root
			# Decrement root's number of comments
			if self.deleted and item_had_root and not item_was_deleted:
				self.root.num_comments -= 1
		
	
	
	
	@classmethod
	def create_or_update(cls, data):
		"""
		Create or update an item given the data from scraping
		If item with id == data['id'] exists, it will be updated with data
		Otherwise, a new item will be created
		This also updates comment counts as needed
		"""
		
		# See if this item already exists
		item = db.session.query(Item).get(data['id'])
		
		# print "Data: "
		# print data
		
		# If found, update this item
		if item is not None:
			item.update(data)
		# Otherwise, create a new item
		else:
			item = Item.create(data)
		
		# print "Item:"
		# print item
		
		# Manually set date_update – this runs even if no new data was available
		item.date_updated = datetime.utcnow()
		
		return item
	
	
	
	
	def find_root(self, touched_ids=None):
		"""
		Find an item's root recursively in the database
		Return None if item is story or root can not be found due to lacking data
		"""
		
		# If story
		if self.parent_id is None:
			# If root() was originally called on this story, return None
			if touched_ids is None:
				return None
			# Otherwise, if root() was first called on a comment, return this story
			else:
				return self
		# If comment
		else:
			# Check that this item has not been recursed over
			if touched_ids is None:
				touched_ids = []
			if self.id in touched_ids:
				raise AppError("Looping parents: %s" % touched_ids)
			touched_ids.append(self.id)
			
			# Return this item's root (recurse if needed)
			if self.parent:
				if self.parent.root:
					return self.parent.root
				else:
					return self.parent.find_root(touched_ids)
			# If parent not found in DB, return None
			else:
				return None
	
	
	
	
	def descendants(self, filters=None, touched_ids=None):
		"""
		Find item's descendants recursively in the database
		filters – dict of conditions that each item must meet
		          these conditions do not apply to item's children, just the item
		          format: {key: value}
		touched_ids – used to track recursion loop. Do not pass this argument
		"""
		
		descendants = []
		if touched_ids is None:
			touched_ids = []
		
		for child in self.children:
			
			# Check that this item has not been recursed over
			if child.id in touched_ids:
				raise AppError("Looping descendants: %s" % touched_ids)
			touched_ids.append(child.id)
			
			# Filter items if requested
			filters_failed = False
			if filters is not None:
				for key, value in filters.iteritems():
					if getattr(child, key) != value:
						filters_failed = True
						break
			
			# Add child only if filter didn't fail
			if not filters_failed:
				descendants.append(child)
			
			# Add child's children in any case
			descendants.extend(child.descendants(filters, touched_ids))
			
		return descendants
	
	
	def comments_url(self):
		"""
		Return Hacker News comments link
		"""
		return 'https://news.ycombinator.com/item?id=%d' % (self.id)
	
	
	def author_url(self):
		"""
		Return Hacker News author link
		"""
		return 'https://news.ycombinator.com/user?id=%s' % (self.author)
	
	
	def main_url(self):
		"""
		Return Link URL if Item has it, or Hacker News comments link otherwise
		"""
		if self.url is None:
			return self.comments_url()
		return self.url
	
	
	def feed_entry(self):
		"""
		Return data representing this item in our RSS/Atom feeds
		Data must be properly encoded for XML
		"""
		
		title = (u'%d – %s' % (self.score, self.title)).encode('ascii', 'xmlcharrefreplace')
		points_label = str(self.score) + (' point' if self.score % 10 == 1 else ' points')
		comments_label = str(self.num_comments) + ' comment' + ('s' if self.num_comments != 1 else '')
		comments_url = self.comments_url().encode('ascii', 'xmlcharrefreplace')
		description = ('<p>%s, <a href="%s">%s</a></p>' % (points_label, comments_url, comments_label)) \
					  .encode('ascii', 'xmlcharrefreplace')
		return {'title': title,
				'title_type': 'html',
				'content': description,
				'content_type': 'html',
				'author': self.author,
				'url': self.main_url(),
				'id': self.comments_url(),
				'updated': self.date_posted, # RSS readers look at this date
				'published': self.date_posted
				}
	
	def json_entry(self):
		"""
		Return data representing this item in our JSON feeds
		"""
		return {'id': self.id,
				'type': self.kind,
				'subtype': self.subkind,
				'author': self.author,
				'title': self.title,
				'body': self.body,
				'score': self.score,
				'num_comments': self.num_comments,
				'domain': self.domain,
				'url': self.main_url(),
				'comments_url': self.comments_url(),
				'date_posted': self.date_posted,
				'date_updated': self.date_updated,
				}
		
		
	








