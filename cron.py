
import flask.ext.script
import sqlalchemy
from datetime import datetime

from hnapp import app, db
from models.item import Item
from scraper import Scraper


manager = flask.ext.script.Manager(app)


@manager.command
def test():
	from scraper import Scraper
	s = Scraper()
	s.connect()
	
	# item_data = s.fetch_item(8549539)
	# print item_data
	# print '<<<'
	# item = s.save_item(item_data)
	
	# from search import Search
	
	# # print Search.token_tree('hello world'.split()), "\n";
	# print Search.token_tree('| | AA | BB | CC | | | | DD | EE |'.split()), "\n";
	# print Search.token_tree('hello the -world host:cnn.com | a | the author:raquo'.split()), "\n";
	# token_tree = Search.token_tree('| | | hello -world - a host:cnn.com | | host:techcrunch.com author:raquo | | |'.split()), "\n";
	# print token_tree
	# token_tree.filter()
	
	return


@manager.command
def fix_ask_items():
	"""Temporary command to fix type:ask items appearing as links with no URL"""
	
	s = Scraper()
	s.connect()
	
	items = (db.session.query(Item)
					   .with_entities(Item.id)
					   .filter(Item.subkind == 'ask')
					   # .filter(Item.raw_body == None)
					   .order_by(sqlalchemy.desc(Item.id))
					   .all()
					   )
	
	# Fetch and save items
	def save(item_data):
		s.save_item(item_data)
		print 'fixed '+str(item_data['id'])
	item_ids = [item.id for item in items]
	s.fetch_items(item_ids, callback=save)


@manager.command
def init():
	s = Scraper()
	s.connect()
	s.save_newest_items()


@manager.command
def update(from_id, to_id, backsort):
	"""
	Update items between given ids
	Use this command to fetch older data
	"""
	
	if from_id is None or not from_id.isdigit() or to_id is None or not to_id.isdigit() or backsort not in ('0', '1'):
		print "Error. Expected parameters from_hn_id to_hn_id backsort (0 or 1)"
		return
	
	s = Scraper()
	s.connect()
	
	# Fetch and save items
	save = lambda item_data: s.save_item(item_data)
	item_ids = range(int(from_id), int(to_id))
	if backsort == '1':
		item_ids = reversed(item_ids)
	s.fetch_items(item_ids, callback=save)
	


@manager.command
def every_1_min():
	
	minute = datetime.utcnow().minute
	s = Scraper()
	s.connect()
	
	if minute % 2 == 0:
		# print "2 MIN"
		# Update scores of newest existing stories
		s.save_newest_existing_stories(count=30, min_delay=90)
	
	if minute % 10 == 0:
		# print "10 MIN"
		# Update scores of stories on pages 2 and of newest
		s.save_newest_existing_stories(start_from=30, count=60, min_delay=5*60)
		# Update scores of stories on pages 2 and 3 of front page
		s.save_top_stories(front_page=False, start_from=30, count=60, min_delay=5*60)
	
	if minute % 5 == 0:
		# print "5 MIN"
		# Discover latest items
		s.save_newest_items()
		# Update scores of front page
		s.save_top_stories(front_page=True, count=30, min_delay=3*60)
	
	# print minute
	# print "ok"


if __name__ == '__main__':
	manager.run()




