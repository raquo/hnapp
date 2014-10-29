# -*- coding: utf-8 -*-

import sqlalchemy
from sqlalchemy import Column, Integer, Numeric, String, Text, Enum, DateTime, ForeignKey
import sqlalchemy.ext.declarative

from datetime import datetime, timedelta

from hnapp import db
from errors import AppError

class Lock(sqlalchemy.ext.declarative.declarative_base()):
	
	__tablename__ = 'lock'
	
	name = Column(String, primary_key=True)
	expires_at = Column(DateTime, default=datetime.utcnow)
	
	
	@classmethod
	def exists(cls, name):
		lock = db.session.query(Lock).get(name)
		return lock and (lock.expires_at is None or lock.expires_at > datetime.utcnow())
	
	
	@classmethod
	def create(cls, name, expires_in=None):
		'''
		expires_in – set expire_at to this number of seconds in the future.
		'''
		
		# %%% FIXME: This commits the session
		# in order for the lock to be visible to other requests
		# This means we can't issue locks after we have begun doing DB work
		# Or we risk accidentally committing something that shouldn't be.
		# We should use a separate session for this, maybe even a SQLite DB.
		
		if len(db.session.dirty) > 0 or len(db.session.deleted) > 0:
			raise AppError('Lock.create – Session is dirty!')
		
		lock = db.session.query(Lock).get(name)
		if not lock:
			lock = Lock()
			lock.name = name
			db.session.add(lock)
			
		if expires_in is not None:
			lock.expires_at = datetime.utcnow() + timedelta(0, expires_in)
		
		db.session.commit()
		
		return lock
	
	
	@classmethod
	def extend(cls, name, expires_in=None):
		'''
		expires_in – set expire_at to this number of seconds in the future.
		'''
		
		# %%% Should expire_at time be updated if the requested time is earlier than it is in DB?
		
		# %%% FIXME: This commits the session (SEE ABOVE)
		
		if len(db.session.dirty) > 0 or len(db.session.deleted) > 0:
			raise AppError('Lock.extend – Session is dirty!')
		
		lock = db.session.query(Lock).get(name)
		if lock:
			if expires_in is not None:
				lock.expires_at = datetime.utcnow() + timedelta(0, expires_in)
			db.session.commit()
		else:
			raise AppError('Lock.extend – Lock %s not found' % name)
	
	
	@classmethod
	def destroy(cls, name):		
		# %%% FIXME: This commits the session (SEE ABOVE)
		
		if len(db.session.dirty) > 0 or len(db.session.deleted) > 0:
			raise AppError('Lock.destroy – Session is dirty!')
		
		lock = db.session.query(Lock).get(name)
		if lock:
			db.session.delete(lock)
			db.session.commit()
	
	
	