# import statements - need to be pip installed in virtual env
import requests
import json
from secrets import *
import sqlite3

DB_NAME = 'articles.db'
SUBJECT_LIST = ['Chemistry', 'Immunology', 'Nutrition', 'Engineering', 'Statistics', 'Psychology', 'Environment', 'Education', 'Law', 'History']

### Caching ###
# open cache file / dictionary, or create new one
CACHE_FNAME = 'finalproj_cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}

# caching helper function
def params_unique_combination(baseurl, params):
    alphabetized_keys = sorted(params.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params[k]))
    return baseurl + "_".join(res)

### Request data from APIs ###

# function to make a request to the Springer Meta API, and cache data
# input: a subject term to search
# return: a list of DOIs for articles retrieved from Springer, or a processed dictionary, or just cache dictionary
def get_springer_data(search_subject):
	baseurl = 'http://api.springer.com/meta/v1/json?'
	params = {}
	params['api_key'] = springer_key # api key is required; imported from secrets.py
	params['q'] = ['keyword:' + search_subject, 'country:"United States"', 'type:Journal'] # defines the query to be performed - many options, case sensitive
	params['p'] = 50

	unique_ident = params_unique_combination(baseurl, params)
	#print(unique_ident)

	if unique_ident in CACHE_DICTION:
		return CACHE_DICTION[unique_ident]

	else:
		resp = requests.get(baseurl, params)
		CACHE_DICTION[unique_ident] = json.loads(resp.text)
		dumped_json_cache = json.dumps(CACHE_DICTION)
		fw = open(CACHE_FNAME,"w")
		fw.write(dumped_json_cache)
		fw.close()
		return CACHE_DICTION[unique_ident]

# return value has a 'records displayed' field that could be good for determining if the result is okay
# may only be able to use one-word subject terms (worked: Mathematics, Chemistry, Psychology, Education)
# has an openaccess parameter that is true / false
# may be able to get subject terms for database from the restatement of the query that's returned in the results


# x = get_springer_data('Geography')
# print(x)

# function to make a request to the PLOS Search API, and cache data
# input: a subject term to search
# return: a list of DOIs articles retrieved from PLOS, or a processed dictionary, or just cache dictionary
def get_plos_data(search_subject):
	baseurl = 'http://api.plos.org/search'
	params = {}
	params['api_key'] = plos_key # api key is required; imported from secrets.py
	params['q'] ='abstract:' + search_subject
	params['rows'] = 50
	params['wt'] = 'json'

	unique_ident = params_unique_combination(baseurl, params)
	#print(unique_ident)

	if unique_ident in CACHE_DICTION:
		return CACHE_DICTION[unique_ident]

	else:
		resp = requests.get(baseurl, params)
		CACHE_DICTION[unique_ident] = json.loads(resp.text)
		dumped_json_cache = json.dumps(CACHE_DICTION)
		fw = open(CACHE_FNAME,"w")
		fw.write(dumped_json_cache)
		fw.close()
		return CACHE_DICTION[unique_ident]


# x = get_plos_data('Ontologies')
# print(x)


# function to make a request to the Semantic Scholar API, and cache data
# input: a doi from a specific article
# return: python dictionary with article-level metrics for that doi
def get_impact_data(doi):
	baseurl = 'https://api.semanticscholar.org/v1/paper/' + doi
	params = {}
	params['include_unknown_references'] = 'true'

	unique_ident = params_unique_combination(baseurl, params)
	#print(unique_ident)

	if unique_ident in CACHE_DICTION:
		return CACHE_DICTION[unique_ident]
	else:
		resp = requests.get(baseurl, params)
		CACHE_DICTION[unique_ident] = json.loads(resp.text)
		dumped_json_cache = json.dumps(CACHE_DICTION)
		fw = open(CACHE_FNAME,"w")
		fw.write(dumped_json_cache)
		fw.close()
		return CACHE_DICTION[unique_ident]


# doi_list = []
# for each in x['records']:
# 	doi = each['doi']
# 	doi_list.append(doi)

# for each in doi_list:
# 	y = get_impact_data(each)
# 	print(y)

### Process API Data ###
# function to process (cached) API data
# input: a subject to search (str)
# return: a dictionary that has only the relevant values for each article, including impact metrics (key=doi, value=relevant data)
def process_api_data(search_subject):
	article_dict = {}

	springer = get_springer_data(search_subject)
	for article in springer['records']:
		doi = article['doi'] 
		title = article['title'].replace('\n', '')
		author = article['creators'][0]['creator']
		date = article['publicationDate'][:4]
		journal = article['publicationName']
		subject = search_subject
		publisher = article['publisher']
		open_access = article['openaccess']
		# add to dictionary
		article_dict[doi] = {'title':title, 'author':author, 'date':date, 'journal':journal, 'subject':subject, 'publisher':publisher, 'open_access':open_access}
		

	plos = get_plos_data(search_subject)
	for article in plos['response']['docs']:
		doi = article['id']
		try:
			title = article['title_display'].replace('\n', '')
			author = article['author_display'][0]
		except:
			title = 'Unknown'
			author = 'Unknown'
		date = article['publication_date'][:4]
		try:
			journal = article['journal']
		except:
			journal = 'Unknown'
		subject = search_subject
		publisher = "PLOS"
		open_access = 'true' 
		article_dict[doi] = {'title':title, 'author':author, 'date':date, 'journal':journal, 'subject':subject, 'publisher':publisher, 'open_access':open_access}


	for doi in article_dict.keys():
		impact = get_impact_data(doi)
		try:
			citation_count = len(impact['citations'])
			influential_citations = impact['influentialCitationCount']
		except:
			citation_count = 'Unknown'
			influential_citations = 'Unknown'
		# update dictionary with the metric data
		article_dict[doi]['metrics'] = {'citations':citation_count, 'influential':influential_citations}

	return article_dict


# article_dict = process_api_data('Mathematics')
# articles2 = process_api_data('Chemistry')
# article_dict.update(articles2)
#print(articles)

# z = process_api_data('Sociology')
# for each in z.keys():
# 	print(z[each]['metrics'])

ARTICLE_DICT = {}
for subject in SUBJECT_LIST:
	articles = process_api_data(subject)
	ARTICLE_DICT.update(articles)


### Store API data in database ###

# DB setup: takes data from the cache dictionary

# function to create a new database - will have two empty tables
# input: database name
# return: nothing
def create_db(dbname):
	try:
		conn = sqlite3.connect(dbname)
	except:
		print("Failed to create database.")

	cur = conn.cursor()

	drop_tables = """ DROP TABLE IF EXISTS 'AccessLevels';            
					DROP TABLE IF EXISTS 'Articles';
					DROP TABLE IF EXISTS 'Subjects';
					"""

	create_tables = """CREATE TABLE 'AccessLevels' (
								'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
								'AccessLevel' TEXT
								); 

						CREATE TABLE 'Articles' (
								'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
								'DOI' TEXT,
								'Title' TEXT,
								'Author' TEXT,
								'PubDate' TEXT,
								'Journal' TEXT,
								'Subject' TEXT,
								'Publisher' TEXT,
								'AccessLevelId' INTEGER,
								'CitationCount' TEXT,
								'InfluentialCitations' TEXT
								);

						CREATE TABLE 'Subjects' (
							'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
							'Subject' TEXT)
							"""

	# call execute statements to create new tables
	cur.executescript(drop_tables)
	cur.executescript(create_tables)

	conn.commit()
	conn.close()
	print('created database')

create_db(DB_NAME)



# function to populate the database
# input: database name
# return: nothing
# populates all three tables in database (AccessLevels, Subjects, Articles)
def populate_db(dbname):
	try:
		conn = sqlite3.connect(dbname)
	except:
		print("Failed to connect to database.")

	cur = conn.cursor()

	statement = """INSERT INTO AccessLevels ('AccessLevel')
					VALUES
					('Open Access'),
					('Subscription Required');
				"""
	cur.execute(statement)

	for subject in SUBJECT_LIST:
		statement = """INSERT INTO Subjects ('Subject')
						VALUES ('{}');
					""".format(subject)
		cur.execute(statement)

	for doi in ARTICLE_DICT.keys():
		if ARTICLE_DICT[doi]['open_access'] == 'false':
			access_id_statement = 'SELECT Id FROM AccessLevels WHERE AccessLevel = "Subscription Required"'
			access_id = cur.execute(access_id_statement).fetchone()[0]
		else:
			access_id_statement = 'SELECT Id FROM AccessLevels WHERE AccessLevel = "Open Access"'
			access_id = cur.execute(access_id_statement).fetchone()[0]
		
		subject_statement = 'SELECT Id FROM Subjects WHERE Subject = "{}"'.format(ARTICLE_DICT[doi]['subject'])
		subject = cur.execute(subject_statement).fetchone()[0]
		
		statement = """INSERT INTO Articles 
						VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
					"""
		values = (None, doi, ARTICLE_DICT[doi]['title'], ARTICLE_DICT[doi]['author'], ARTICLE_DICT[doi]['date'], ARTICLE_DICT[doi]['journal'], 
				  subject, ARTICLE_DICT[doi]['publisher'], access_id, ARTICLE_DICT[doi]['metrics']['citations'], ARTICLE_DICT[doi]['metrics']['influential'])
		cur.execute(statement, values)

	conn.commit()
	conn.close()
	print('populated database')


populate_db(DB_NAME)


### Present data ###

# plotly functions
# may also need functions to process data - create dictionaries for each data presentation option from the database, to draw from for plotly


### Invoke functions to gather data from APIs and populate database ###
# print('Gathering journal article citation data...')

# print('Populating database articles.db...')


### Make it interactive ###
# input:
# return:
# what this function does:
# - let user choose data presentation options
def interactive_commands():
	pass
	# enter four subjects: 
	# create a default list - Education, Psychology, Mathematics, Chemistry
	# have a detailed help list
	# also have a .txt file of a subject list, to load in like the help file in project 3, to show possible 1-word subjects



