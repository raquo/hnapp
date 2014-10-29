# -*- coding: utf-8 -*-

import sqlalchemy
from sqlalchemy import Column, Integer, Numeric, String, Text, Enum, DateTime, ForeignKey
import sqlalchemy.ext.declarative

# from datetime import datetime

from hnapp import db
from errors import AppError


class Status(sqlalchemy.ext.declarative.declarative_base()):
	
	__tablename__ = 'status'
	
	name = Column(Integer, primary_key=True)
	
	number = Column(Integer)
	text = Column(Text)
	date = Column(DateTime)
	
	
	@classmethod
	def get_max_item_id(cls):
		
		row = db.session.query(cls).get('last_item_id')
		
		AppError.makesure(row is not None, "status.last_item_id not found in DB")
		AppError.makesure(row.number > 0, "status.last_item_id.number is not defined in DB")
		
		return row.number
	
	
	@classmethod
	def set_max_item_id(cls, item_id):
		
		row = db.session.query(cls).get('last_item_id')
		
		AppError.makesure(row is not None, "status.last_item_id not found in DB")
		AppError.makesure(item_id > 0, "status.last_item_id.number must be set to a positive number")
		AppError.makesure(item_id >= row.number, "status.last_item_id.number must not be decremented")
		
		row.number = item_id
		db.session.add(row)
	
	
	









