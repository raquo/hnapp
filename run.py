
# Load app

from hnapp import app

# Only flask dev server calls this
# uwsgi handles app object by itself
if __name__ == '__main__':
	app.run('0.0.0.0', 8000)
