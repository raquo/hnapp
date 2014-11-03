# -*- coding: utf-8 -*-

# import flask
# import requests
# import json
# import lxml.html
# import re
# from firebase import firebase
# from urlparse import urlparse, urljoin
# from datetime import datetime
import sqlalchemy
from sqlalchemy import func
# import bleach

from hnapp import app, db
from models.item import Item
# from models.status import Status
from errors import AppError, QueryError




class Search(object):
	
	@classmethod
	def token_from_word(cls, word):
		"""Parse word into a SearchToken"""
		
		negate = (word[0] == '-')
		word = word[1:] if negate else word
		for prefix, params in SearchToken.types.iteritems():
			if word.lower().startswith(prefix):
				if params.get('type', None) == 'join':
					if prefix == word and not negate: # negating joins is not valid
						print '>>>>>J', prefix
						token = SearchJoin(prefix=prefix)
					else:
						print '>>>>JW', prefix
						token = SearchToken(prefix='word:', value=word, negate=negate)
				else:
					print '>>>>>>', prefix, negate
					token = SearchToken(prefix=prefix, value=word[len(prefix):], negate=negate)
				break
		else:
			print '>>>>>W', prefix, negate
			token = SearchToken(prefix='word:', value=word, negate=negate)
		return token # if token.validate() else None
		
	
	
	@classmethod
	def token_tree(cls, words):
		"""Generate a token tree from a list of words"""
		
		# print "WORDS: ", words
		
		tokens = []
		token_tree = []
		
		# Generate tokens
		for word in words:
			tokens.append(cls.token_from_word(word))
		
		# Remove bad OR operators
		for ix, token in reversed(list(enumerate(tokens))):
			if isinstance(token, SearchJoin):
				if ix == 0 or ix == len(tokens)-1:
					del tokens[ix]
				elif isinstance(tokens[ix-1], SearchJoin):
					del tokens[ix]
		
		# print 'TOKENS: ', tokens
		
		# Compile token tree
		while(len(tokens) > 0):
			
			# Handle subsequent join operators
			# Special case for sequences like a | b | c | d ...
			# This will compile to |(a, b, c, d) instead of a nested structure
			if len(tokens) >= 2:
				if isinstance(tokens[0], SearchJoin):
					prev_token = token_tree[0]
					if isinstance(prev_token, SearchJoin) and prev_token.prefix == tokens[0].prefix:
						# print 'appending %s with %s' % (prev_token, tokens[1])
						prev_token.tokens.append(tokens[1])
					else:
						tokens[0].tokens = [prev_token, tokens[1]]
						token_tree.append(tokens[0])
					del tokens[0]
					del tokens[0]
					continue
			
			# Handle lone join operator
			if len(tokens) >= 3:
				if isinstance(tokens[1], SearchJoin):
					tokens[1].tokens = [tokens[0], tokens[2]]
					token_tree.append(tokens[1])
					del tokens[0]
					del tokens[0]
					del tokens[0]
					continue
			
			# Handle non-join token
			token_tree.append(tokens[0])
			del tokens[0]
		
		
		# print 'TREE: ', token_tree
		
		# Clean up token tree
		errors = []
		token_tree = SearchJoin(prefix='&', tokens=token_tree)
		token_tree = cls.clean_join(token_tree, errors)
		
		# print "ERRORS:", errors
		# print "TREE:", token_tree
		
		return token_tree
	
	
	@classmethod
	def clean_join(cls, join, errors):
		"""
		Remove non-validating tokens, such as single stop-words
		Un-nest (remove) joins that contain only one token as a result of this cleanup
		"""
		
		# Remove non-validating tokens
		# print "CLEAN:", join
		for ix, token in reversed(list(enumerate(join.tokens))):
			
			# Recurse into nested joins
			if isinstance(token, SearchJoin):
				# print "JOIN<<<<"
				clean_token = cls.clean_join(token, errors)
				if clean_token is None:
					del join.tokens[ix]
				else:
					join.tokens[ix] = clean_token
			
			# Check that the token validates
			else:
				try:
					# <<< This could be more efficient, maybe – filter() call only for validation
					if token.filter() is None:
						# print "--- Token removed: %s" % token
						del join.tokens[ix]
				except QueryError as e:
					errors.append(e)
					del join.tokens[ix]
		
		# Un-nest (remove) joins that only contain one token
		if len(join.tokens) > 1:
			return join
		elif len(join.tokens) == 1:
			return join.tokens[0]
		else:
			return None
	
	
	@classmethod
	def query(cls, text_query):
		"""..."""
		
		token_tree = cls.token_tree(text_query.split())
		
		query = (db.session.query(Item)
						   # .filter(Item.kind == 'story')
						   .filter(Item.dead == 0)
						   .filter(Item.deleted == 0)
						   )
		if token_tree is not None:
			query = query.filter(token_tree.filter())
		
		query = query.order_by(sqlalchemy.desc(Item.id)).slice(0, 30)
		
		return query
	
	
	



class SearchToken(object):
	
	types = {
		'|': {'type': 'join'},
		'word:': {},
		'author:': {},
		'host:': {},
		'type:': {},
		'score>': {},
		'score<': {},
		'comments>': {},
		'comments<': {}
		}
	
	prefix = None
	value = None
	negate = False
	
	
	
	def __init__(self, prefix=None, value=None, negate=False):
		self.prefix = prefix
		self.value = value
		self.negate = negate
	
	
	
	def filter(self):
		"""
		Return token filter for use in SQLAlchemy query
		"""
		
		# print 'filter for token:', self, self.prefix
		
		if self.prefix == 'word:':
			tsquery = db.session.execute(sqlalchemy.sql.select([func.plainto_tsquery('english', self.value)])).fetchone()[0]
			if tsquery != '':
				where_story = sqlalchemy.and_(Item.kind == 'story', Item.title_tsv.match(tsquery))
				where_comment = sqlalchemy.and_(Item.kind == 'comment', Item.body_tsv.match(tsquery))
				where = sqlalchemy.or_(where_story, where_comment)
			else:
				# print 'empty word: %s' % self.value
				return None
		
		elif self.prefix == 'author:':
			if self.value != '':
				# print 'ok author'
				where = (func.lower(Item.author) == self.value.lower())
			else:
				# print 'empty author: %s' % self.value
				return None
		
		elif self.prefix == 'host:':
			if self.value != '':
				# print 'ok host'
				if self.value[:4] == 'www.':
					host = self.value[4:]
				else:
					host = self.value
				where = (Item.domain == host.lower())
			else:
				# print 'empty host: %s' % self.value
				return None
		
		elif self.prefix == 'type:':
			value = self.value.lower()
			if value == 'story':
				where = (Item.kind == value)
			elif value in ('comment', 'link', 'job', 'poll', 'ask', 'show'):
				where = (Item.subkind == value)
			else:
				return None
		
		# <<< Not sure if this should exist.
		# elif self.prefix == 'front:':
		# 	if self.value == 'yes':
		# 		where = (Item.date_entered_fp != None) # SQLAlchemy == operator (not "is")
		# 	elif self.value == 'no':
		# 		where = (Item.date_entered_fp == None) # SQLAlchemy == operator (not "is")
		# 	else:
		# 		return None
		
		elif self.prefix == 'score>':
			if self.value.isdigit():
				where = (Item.score > int(self.value.lstrip('0')))
			else:
				return None
		
		elif self.prefix == 'score<':
			if self.value.isdigit():
				where = (Item.score < int(self.value.lstrip('0')))
			else:
				return None
		
		elif self.prefix == 'comments>':
			if self.value.isdigit():
				where = (Item.num_comments > int(self.value.lstrip('0')))
			else:
				return None
		
		elif self.prefix == 'comments<':
			if self.value.isdigit():
				where = (Item.num_comments < int(self.value.lstrip('0')))
			else:
				return None
		
		else:
			raise AppError(u'Token prefix not found: %s' % self.prefix)
		
		
		if self.negate:
			return sqlalchemy.not_(where)
		else:
			return where
		
	
	
	def __repr__(self):
		return u'<%s(%s%s %s)>' % (self.__class__.__name__, 'NOT ' if self.negate else '', self.prefix, self.value)







class SearchJoin(SearchToken):
	
	tokens = []
	
	
	
	def __init__(self, prefix=None, tokens=None):
		self.prefix = prefix
		self.tokens = tokens
	
	
	
	def filter(self):
		"""
		Return filter for use in SQLAlchemy query
		Calls itself recursively to handle joins
		"""
		
		if len(self.tokens) == 0:
			raise QueryError('Operator %s has no sides' % self.prefix)
		filters = []
		operators = {
			'|': sqlalchemy.or_,
			'&': sqlalchemy.and_
			}
		
		for token in self.tokens:
			filters.append(token.filter())
		
		return operators[self.prefix](*filters)
	
	
	
	def __repr__(self):
		return u'<%s(%s, %s)>' % (self.__class__.__name__, self.prefix, self.tokens)



