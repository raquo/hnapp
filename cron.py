
import flask.ext.script
from datetime import datetime

from hnapp import app
from scraper import Scraper


manager = flask.ext.script.Manager(app)


@manager.command
def test():
	from search import Search
	
	# print Search.token_tree('hello world'.split()), "\n";
	print Search.token_tree('| | AA | BB | CC | | | | DD | EE |'.split()), "\n";
	print Search.token_tree('hello the -world host:cnn.com | a | the author:raquo'.split()), "\n";
	token_tree = Search.token_tree('| | | hello -world - a host:cnn.com | | host:techcrunch.com author:raquo | | |'.split()), "\n";
	print token_tree
	# token_tree.filter()
	
	return


@manager.command
def init():
	s = Scraper()
        s.connect()
	s.save_newest_items()

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




