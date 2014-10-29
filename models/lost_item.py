# -*- coding: utf-8 -*-

import sqlalchemy
from sqlalchemy import Column, Integer, Numeric, String, Text, Enum, DateTime, ForeignKey
import sqlalchemy.ext.declarative

from datetime import datetime


class LostItem(sqlalchemy.ext.declarative.declarative_base()):
	
	__tablename__ = 'lost_item'
	
	id = Column(Integer, primary_key=True)
	reason = Column(String)
	response = Column(Text, nullable=True, default=None)
	traceback = Column(Text, nullable=True, default=None)
	date_found = Column(DateTime, default=datetime.utcnow)
	


