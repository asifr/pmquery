# -*- coding: utf-8 -*-
#!/usr/bin/env python
'''
pmquery - Query PubMed and download results to text files

## Requirements

If you don't have the pip utility first install it with:
> easy_install pip

Install all the mandatory dependencies by typing:
> pip install -r requirements.txt

## Usage
Before running the script make sure you edit the config file.
The `term` and `ident` parameters indicate the search term
and a unique identifier (no spaces allowed), respectively.

To execute the script pmquery uses a Makefile, although
executing the python script will produce the same results.

1	Query the database:
	> make query
		or
	> python pmquery.py
2.	Delete all data folders, this preserves zipped archives
	but removes the individual text files:
	> make clean

Copyright (c) 2013— Asif Rahman
License: MIT (see LICENSE for details)
'''

__author__ = 'Asif Rahman'
__version__ = (0, 1, 0, '')
__license__ = 'MIT'

from os import path, makedirs
import requests
from xml.dom import minidom
import json
import time
from ConfigParser import RawConfigParser
import logging
import subprocess

VERSION_STRING = '%d.%d.%d%s' % __version__

# Figure out installation directory
installation_dir, _ = path.split(path.abspath(__file__))

# Set up configuration settings
config = RawConfigParser()
config.read(path.join(installation_dir, 'config'))

logging.basicConfig(
	filename	= config.get('log', 'filename'),
	level		= getattr(logging, config.get('log', 'level')),
	format		= config.get('log', 'format'),
	datefmt		= config.get('log', 'datefmt')
)

logging.getLogger("requests").setLevel(logging.WARN)

# Shared logger instance
log = logging.getLogger()

term = config.get('search', 'term')
data_dir = path.join(installation_dir, config.get('data', 'dirname'))
query_results_dir = path.join(installation_dir, config.get('data', 'dirname'), config.get('search', 'ident'))

if not path.exists(query_results_dir):
	makedirs(query_results_dir)

email = 'email@yourdomain.com'
tool = 'pmquery'
database = 'pubmed'
retmax = 100
retmode = 'xml'
retstart = 0

def parse_xml(elm, idx, default):
	try:
		if idx != None:
			elm = elm[idx]
		elm = elm.childNodes[0].data
		return elm
	except Exception:
		elm = default
		return elm
		pass
	else:
		elm = default
		return elm

def text_output(xml,count):
	"""Returns JSON-formatted text from the XML retured from E-Fetch"""
	xmldoc = minidom.parseString(xml.encode('utf-8').strip())

	jsonout = []
	for i in range(count):
		title = ''
		title = xmldoc.getElementsByTagName('ArticleTitle')
		title = parse_xml(title, i, '')

		pmid = ''
		pmid = xmldoc.getElementsByTagName('PMID')
		pmid = parse_xml(pmid, i, '')

		abstract = ''
		abstract = xmldoc.getElementsByTagName('AbstractText')
		abstract = parse_xml(abstract, i, '')

		try:
			authors = xmldoc.getElementsByTagName('AuthorList')
			authors = authors[i].getElementsByTagName('Author')

			authorlist = []
			for author in authors:
				LastName = author.getElementsByTagName('LastName')
				LastName = parse_xml(LastName, 0, '')
				Initials = author.getElementsByTagName('Initials')
				Initials = parse_xml(Initials, 0, '')
				if LastName != '' and Initials != '':
					author = '%s, %s' % (LastName, Initials)
				else:
					author = ''
				authorlist.append(author)
		except Exception:
			authorlist = []
			pass

		try:
			journalinfo = xmldoc.getElementsByTagName('Journal')[i]
			journalIssue = journalinfo.getElementsByTagName('JournalIssue')[0]
		except Exception:
			journalinfo = None
			journalIssue = None
			pass

		journal = ''
		year = ''
		volume = ''
		issue = ''
		pages = ''
		if journalinfo != None:
			journal = parse_xml(journalinfo.getElementsByTagName('Title'), 0, '')

			year = journalIssue.getElementsByTagName('Year')
			year = parse_xml(year, 0, '')
			volume = journalIssue.getElementsByTagName('Volume')
			volume = parse_xml(volume, 0, '')
			issue = journalIssue.getElementsByTagName('Issue')
			issue = parse_xml(issue, 0, '')
			pages = xmldoc.getElementsByTagName('MedlinePgn')
			pages = parse_xml(pages, 0, '')

		jsonout.append({
					'pmid':pmid,
					'title':title,
					'authors':authorlist,
					'journal':journal,
					'year':year,
					'volume':volume,
					'issue':issue,
					'pages':pages,
					'abstract':abstract
				})
	return json.dumps(jsonout)

# Prepare to query E-Search
utilsparams = {
	'db':database,
	'tool':tool,
	'email':email,
	'term':term,
	'usehistory':'y',
	'retmax':retmax,
	'retstart':retstart
}

url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
r = requests.get(url, params = utilsparams)
data = r.text
xmldoc = minidom.parseString(data)
ids = xmldoc.getElementsByTagName('Id')

if len(ids) == 0:
	print 'QueryNotFound'
	exit()

count = xmldoc.getElementsByTagName('Count')[0].childNodes[0].data
itr = int(count)/retmax

# Save some general information about this query
dest = data_dir + '/' + config.get('search','ident') + '.json'
f = open(dest, 'w+')
f.write(json.dumps({'term':term,'ident':config.get('search','ident'),'count':count,'mtime':int(time.time())}))
f.close()

# Write text files containing results from E-Fetch
for x in xrange(0,itr+1):
	retstart = x*utilsparams['retmax']

	utilsparams['retstart'] = retstart

	url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
	r = requests.get(url, params = utilsparams)
	data = r.text
	xmldoc = minidom.parseString(data)
	ids = xmldoc.getElementsByTagName('Id')

	id = []
	for i in ids:
		id.append(i.childNodes[0].data)

	fetchparams = {
		'db':database,
		'tool':tool,
		'email':email,
		'id':','.join(id),
		'retmode':retmode
	}

	url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'
	r = requests.get(url, params = fetchparams)
	data = r.text

	s = text_output(data,retmax)
	dest = query_results_dir + '/query_results_%i.json' % retstart
	f = open(dest, 'w+')
	f.write(s)
	f.close()

# Create a zipped archive of the data
PIPE = subprocess.PIPE
pd = subprocess.Popen(['/usr/bin/zip', '-r', config.get('search','ident'), config.get('search','ident'), config.get('search','ident') + '.json'],
						stdout=PIPE, stderr=PIPE, cwd=data_dir)
stdout, stderr = pd.communicate()