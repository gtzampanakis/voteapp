import os, datetime, urllib, contextlib, copy, itertools, logging, json
import MySQLdb
import cherrypy as cp
import mako
import mako.lookup
import dbapiutil

ROOT_DIR = os.path.dirname(__file__)

lookup = mako.lookup.TemplateLookup(
			directories = os.path.join(ROOT_DIR, '..', 'templates'))

def get_conn():
	with open(os.environ.get('VOTEAPP_CONFIG_PATH')) as f:
		connect_parameters = json.load(f)
	conn = dbapiutil.connect(
			lambda: MySQLdb.connect(**connect_parameters)
	)
	return conn

class Application:

	@cp.expose
	def vote(self, *args, **kwargs):

		template = lookup.get_template('index.html')
		return template.render()

	@cp.expose
	def results(self, *args, **kwargs):
		cp.response.headers['content-type'] = 'application/json'
		with get_conn() as conn:
			sql = '''
				select count(*), rfndum
				from votes
				where rfndum in ('yes', 'no')
				order by rfndum
			'''

			no_votes = 0
			yes_votes = 0

			standings = {'yes': 0, 'no': 0}

			for row in conn.execute(sql):
				standings[row[1]] = row[0]

			return json.dumps({'standings': standings})


	@cp.expose
	def submitvote(self, *args, **kwargs):
		cp.response.headers['content-type'] = 'application/json'
		lastelect, rfnd = args

		with get_conn() as conn:

			### sql_check_ip = 'select * from votes where ip = %s'
			### if conn.execute(sql_check_ip, [cp.request.remote.ip]).fetchone():
			### 	cp.response.status = 401
			### 	return json.dumps({'error': 'ALREADYVOTED'})

			### sql_check_host = 'select * from votes where host = %s'
			### if conn.execute(sql_check_ip, [cp.request.remote.name]).fetchone():
			### 	cp.response.status = 401
			### 	return json.dumps({'error': 'ALREADYVOTED'})
			if cp.session.get('voted') == '1':
				cp.response.status = 401
				return json.dumps({'error': 'ALREADYVOTED'})

			sql = '''
				insert into votes
				(party, rfndum, ip, host, createdat)
				values
				(%s, %s, %s, %s, current_timestamp)
			'''
			conn.execute(sql, [lastelect, rfnd, cp.request.remote.ip, cp.request.remote.name])
			cp.session['voted'] = '1'


		return json.dumps({'error': ''})

