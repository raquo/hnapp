
from hnapp import app

def debug_print(*items):
	if items and app.config['DEBUG']:
		print ' '.join([str(item) for item in items])