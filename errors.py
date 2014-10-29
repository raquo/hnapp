# -*- coding: utf-8 -*-

# class SchedulerError(Exception):
# 	pass

class AppError(Exception):
	
	@staticmethod
	def makesure(test, message='Generic makesure failed'):
		if not test:
			raise AppError(message)

class ValidationError(AppError):
	pass

class ScraperError(AppError):
	pass

class QueryError(AppError):
	pass














