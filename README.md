hnapp
=====

hnapp is a search engine for Hacker News that lets you subscribe to new search results via RSS or JSON. So, you would use it to keep in the loop about your favourite technologies, keep an eye on mentions of your product, filter out politics, or follow what smart people say. See [hnapp.com](http://hnapp.com) for more examples.

This repository contains the source code for all of hnapp, including the website [hnapp.com](http://hnapp.com).


What's in the box
-----------------

- Mobile and web interfaces
- RSS and JSON feeds
- Full text search with stemming, as well as search constraints (e.g. score>10). For search syntax, see [hnapp.com](http://hnapp.com)
- Hacker News data is retrieved from the [official Firebase API](https://github.com/HackerNews/API).


Dependencies
------------

- ```python``` 2.7/2.8, ```python-dev```, ```virtualenv```, ```setuptools```
- ```postgresql```, ```postgresql-common```, ```libpq-dev```
- ```nodejs```, ```npm```, ```bower```
- Also see ```requirements.txt``` for pip


Environment
-----------
hnapp was tested in the following environment:
- Ubuntu 12.04 and 14.04
- ```nginx``` + ```uwsgi``` combo for production, or Flask's built-in web server for development


Installation
------------

1. Install all dependencies. Install python stuff into a virtualenv.
2. Create postgresql user and database
```bash
sudo su - postgres
psql -U postgres -c "CREATE USER hnapp WITH PASSWORD 'new_password'"
psql -U postgres postgres -f /srv/www/hnapp/sql/schema.sql
psql
```
3. Grant permissions to the new user (run this in psql)
```sql
\c hnapp
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES in schema public TO hnapp
INSERT INTO status (name, number) values ('last_item_id', XXXXXXX)
```
Where XXXXXXX is the id of the first HN item you want hnapp to download. Don't set it too far in the past, you can always download more items later.
4. Install dependencies from bower.json
5. Install python dependencies using pip if you haven't done so yet:
```bash
pip install -r requirements.txt
```
6. Create a config file and edit it as per instructions within
```bash
cp config.sample.py config.py
nano config.py
```
7. Set up a cron job to run ```vpython /srv/www/hnapp/cron.py every_1_min``` every minute (replace ```vpython``` with the path to the python binary in your virtual environment). You should redirect all output to a log file to log errors.
8. Connect hnapp to a web server. The directory ```static``` must be webroot. hnapp was tested with ```nginx``` and ```uwsgi```. The uwsgi application is ```app``` in ```run.py```. For development purposes, you can use Flask's built-in web server by running ```vpython run.py```


License
--------------------------------
MIT License, see LICENSE.md


Contact
-------
For bug reports and feature requests, please open an issue on github.

Nikita Gazarov

[nikita@raquo.com](mailto:nikita@raquo.com)

[@raquo](http://twitter.com/raquo) [@hnapp](http://twitter.com/hnapp)

