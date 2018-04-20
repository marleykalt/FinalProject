# import statements
import requests
import json
from secrets import *
import sqlite3
import random
import sys
import plotly.plotly as py
import plotly.graph_objs as go


### Define global variables - will use these several times ###
CACHE_FNAME = 'finalproj_cache.json'
DB_NAME = 'articles.db'
SUBJECT_LIST = ['Chemistry', 'Immunology', 'Nutrition', 'Engineering', 'Statistics', 'Psychology', 'Environment', 'Education', 'Law', 'History']
ARTICLE_DICT = {}

### Caching Setup ###
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

# function to make a request to the Springer Meta API
# input: a subject term to search
# return: python dictionary, from cache
def get_springer_data(search_subject):
	baseurl = 'http://api.springer.com/meta/v1/json?'
	params = {}
	params['api_key'] = springer_key # api key is required; variable imported from secrets.py
	params['q'] = ['keyword:' + search_subject, 'country:"United States"', 'type:Journal'] # defines the query to be performed
	params['p'] = 50

	unique_ident = params_unique_combination(baseurl, params)

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


# function to make a request to the PLOS Search API
# input: a subject term to search
# return: python dictionary, from cache
def get_plos_data(search_subject):
	baseurl = 'http://api.plos.org/search'
	params = {}
	params['api_key'] = plos_key # api key is required; variable imported from secrets.py
	params['q'] ='abstract:' + search_subject
	params['rows'] = 50
	params['wt'] = 'json'

	unique_ident = params_unique_combination(baseurl, params)

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


# function to make a request to the Semantic Scholar API
# input: a doi from a specific article
# return: python dictionary with article-level metrics for that doi, from cache
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


### Set up Article and Subject classes ###
# these classes will take queried data from the articles database
# will prepare data for visualization

class Subject():
	def __init__(self, subject, citation_count, influential_count):
		self.subject = subject
		self.avg_citations = citation_count
		self.avg_influential = influential_count

	def __str__(self):
		return "{}: {} citation(s) (average), {} influential citation(s) (average)".format(self.subject, self.avg_citations, self.avg_influential)

class Article():
	def __init__(self, subject, year, access_level, citation_count, influential_count):
		self.subject = subject
		self.year = year
		self.access = access_level
		self.citations = citation_count
		self.influential = influential_count

	def __str__(self):
		return "Subject: {} ({}), Access: {} - {} citation(s), {} influential citation(s)".format(self.subject, self.year, self.access, 
																								self.citations, self.influential)


### Process API Data ###

# function to fetch and process API data
# input: a subject to search
# return: a dictionary that has only the relevant values (for data viz) for each article, including impact metrics (key=doi:value=relevant data)
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
		article_dict[doi] = {'title':title, 'author':author, 'date':date, 'journal':journal, 'subject':subject, 'publisher':publisher, 
							'open_access':open_access}
		

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
		article_dict[doi] = {'title':title, 'author':author, 'date':date, 'journal':journal, 'subject':subject, 'publisher':publisher, 
							'open_access':open_access}


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


### Store API data in database ###

# function to create a new database
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
								'SubjectId' INTEGER,
								'Publisher' TEXT,
								'AccessLevelId' INTEGER,
								'CitationCount' BLOB,
								'InfluentialCitations' BLOB
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


# function to populate all three tables in database (AccessLevels, Subjects, Articles)
# input: database name
# return: nothing
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


### Process Data ###
### Functions to create class instances or query the database, to use when creating charts to present data ###

# function to query the database to get average citations, grouped by access level
# input: database name
# return: list of two tuples: [(access_level, avg_citations), (access_level, avg_citations)]
def get_citations_by_access(dbname):
	conn = sqlite3.connect(dbname)
	cur = conn.cursor()

	statement = """SELECT C.AccessLevel, AVG(A.CitationCount)
					FROM Articles as A
					JOIN AccessLevels as C
					ON A.AccessLevelId = C.Id
					WHERE A.CitationCount IS NOT 'Unknown'
					GROUP BY C.AccessLevel """
	results = cur.execute(statement).fetchall()
	conn.commit()
	conn.close()
	return results

# function to query the database to get average number of influential citations, grouped by access level
# input: database name
# return: list of two tuples
def get_influence_by_access(dbname):
	conn = sqlite3.connect(dbname)
	cur = conn.cursor()

	statement = """SELECT C.AccessLevel, AVG(A.InfluentialCitations)
					FROM Articles as A
					JOIN AccessLevels as C
					ON A.AccessLevelId = C.Id
					WHERE A.InfluentialCitations IS NOT 'Unknown'
					GROUP BY C.AccessLevel """
	results = cur.execute(statement).fetchall()
	conn.commit()
	conn.close()
	return results

# function to query the database to get average number of citations, grouped by publication date
# input: database name
# return: list of tuples
def get_citations_by_year(dbname):
	conn = sqlite3.connect(dbname)
	cur = conn.cursor()

	statement = """SELECT PubDate, AVG(CitationCount)
					FROM Articles 
					WHERE CitationCount IS NOT 'Unknown'
					GROUP BY PubDate """
	results = cur.execute(statement).fetchall()
	conn.commit()
	conn.close()
	return results

# function to query the database and create instances of the Subject class
# input: name of database
# return: a list of Subject class instances
def create_subject_insts(dbname):
	avg_cite_by_sub = []

	conn = sqlite3.connect(dbname)
	cur = conn.cursor()

	statement = """ SELECT S.Subject, Avg(A.CitationCount), AVG(A.InfluentialCitations)
					FROM Articles as A
						JOIN Subjects as S
							ON A.SubjectId = S.Id 
						JOIN AccessLevels as C
							ON A.AccessLevelId = C.Id
					WHERE CitationCount IS NOT 'Unknown'
					GROUP BY S.Subject """

	results = cur.execute(statement).fetchall()

	for row in results:
		subject_obj = Subject(*row)
		avg_cite_by_sub.append(subject_obj)

	conn.commit()
	conn.close()
	return avg_cite_by_sub


# function to query the database and create instances of the Article class
# input: name of database
# return: a list of Article class instances
def create_article_insts(dbname):
	article_obs = []

	conn = sqlite3.connect(dbname)
	cur = conn.cursor()

	statement = """ SELECT S.Subject, A.PubDate, C.AccessLevel, A.CitationCount, A.InfluentialCitations
					FROM Articles as A
						JOIN Subjects as S
							ON A.SubjectId = S.Id 
						JOIN AccessLevels as C
							ON A.AccessLevelId = C.Id
					WHERE CitationCount IS NOT 'Unknown'"""

	results = cur.execute(statement).fetchall()

	for row in results:
		article_obj = Article(*row)
		article_obs.append(article_obj)

	conn.commit()
	conn.close()
	return article_obs


### Present data ###
### Four Plotly functions to show different data presentation options ###

# Function 1: plots the average citations for articles based on access level
# input: list of two tuples - each tuple has access level and average citation count
# return: nothing, but opens a graph in plotly in a web browser
def plot_access_citations(access_citation_list):
	trace0 = go.Bar(
    x=[access_citation_list[0][0], access_citation_list[1][0]],
    y=[access_citation_list[0][1], access_citation_list[1][1]],
    text=['%.1f'%access_citation_list[0][1] + " citations on average", '%.1f'%access_citation_list[1][1] + " citations on average"],
    marker=dict(
        color='rgb(17,70,155)',
        line=dict(
            color='rgb(8,48,107)',
            width=1.0,
        )
    ),
)

	data = [trace0]
	layout = go.Layout(
	    title='Average Article Citations by Access Level',
	)

	fig = go.Figure(data=data, layout=layout)
	py.plot(fig, filename='citations-by-access')


# Function 2: plots the average number of influential  citations for articles based on access level
# input: list of two tuples - each tuple has access level and average influential citation count
# return: nothing, but opens a graph in plotly in a web browser
def plot_influential_citations(access_influence_list):
	trace0 = go.Bar(
    x=[access_influence_list[0][0], access_influence_list[1][0]],
    y=[access_influence_list[0][1], access_influence_list[1][1]],
    text=['%.1f'%access_influence_list[0][1] + " influential citations on average", 
    	  '%.1f'%access_influence_list[1][1] + " influential citations on average" ],
    marker=dict(
        color='rgb(17,70,155)',
        line=dict(
            color='rgb(8,48,107)',
            width=1.0,
        )
    ),
)

	data = [trace0]
	layout = go.Layout(
	    title='Average Number of Influential Citations by Access Level',
	)

	fig = go.Figure(data=data, layout=layout)
	py.plot(fig, filename='influence-by-access')


# Function 3: plots average citation count for articles, grouped by subject
# input: a list of Subject class instances
# return: nothing, but opens a graph in plotly in a web browser
def plot_citations_by_subject(subject_inst_list):
	# separate subject instances by general area of study
	sci_math = ['Chemistry', 'Immunology', 'Nutrition', 'Engineering', 'Statistics', 'Psychology', 'Environment']
	hum = ['Education', 'Law', 'History']
	sub1 = []
	sub2 = []
	for inst in subject_inst_list:
		if inst.subject in sci_math:
			sub1.append(inst)
		if inst.subject in hum:
			sub2.append(inst)

	trace1 = go.Bar(
    x=[sub1[0].subject, sub1[1].subject, sub1[2].subject, sub1[3].subject, sub1[4].subject, sub1[5].subject, sub1[6].subject], 
    y=[sub1[0].avg_citations, sub1[1].avg_citations, sub1[2].avg_citations, sub1[3].avg_citations, sub1[4].avg_citations, 
    	sub1[5].avg_citations, sub1[6].avg_citations],
    text=['%.1f'%sub1[0].avg_citations + " citations on average", '%.1f'%sub1[1].avg_citations + " citations on average", 
    	'%.1f'%sub1[2].avg_citations + " citations on average", '%.1f'%sub1[3].avg_citations + " citations on average", 
    	'%.1f'%sub1[4].avg_citations + " citations on average", '%.1f'%sub1[5].avg_citations + " citations on average", 
    	'%.1f'%sub1[6].avg_citations + " citations on average",],
    name='Science/Mathematics',
    marker=dict(
        color='rgb(17,70,155)'
    )
)
	trace2 = go.Bar(
    x=[sub2[0].subject, sub2[1].subject, sub2[2].subject],
    y=[sub2[0].avg_citations, sub2[1].avg_citations, sub2[2].avg_citations],
    text=['%.1f'%sub2[0].avg_citations + " citations on average", '%.1f'%sub2[1].avg_citations + " citations on average", 
    	'%.1f'%sub2[2].avg_citations + " citations on average"],
    name='Humanities/Liberal Arts',
    marker=dict(
        color='rgb(237,61,52)'
    )
)

	data = [trace1, trace2]
	layout = go.Layout(
	    title='Average Article Citations by Subject',
	)

	fig = go.Figure(data=data, layout=layout)
	py.plot(fig, filename='citations-by-subject')


# Function 4: plots average citation counts for articles, grouped by year
# input: list of tuples
# return: nothing, but opens a graph in plotly in a web browser
def plot_citations_by_year(year_citation_list):
	trace0 = go.Bar(
    x=[year_citation_list[0][0], year_citation_list[1][0], year_citation_list[2][0], year_citation_list[3][0], year_citation_list[4][0], 
    year_citation_list[5][0], year_citation_list[6][0], year_citation_list[7][0], year_citation_list[8][0], year_citation_list[9][0], 
    year_citation_list[10][0], year_citation_list[11][0]],
    
    y=[year_citation_list[0][1], year_citation_list[1][1], year_citation_list[2][1], year_citation_list[3][1], year_citation_list[4][1], 
    year_citation_list[5][1], year_citation_list[6][1], year_citation_list[7][1], year_citation_list[8][1], year_citation_list[9][1], 
    year_citation_list[10][1], year_citation_list[11][1]],
    text=['%.1f'%year_citation_list[0][1] + " citations on average", '%.1f'%year_citation_list[1][1] + " citations on average", 
    	'%.1f'%year_citation_list[2][1] + " citations on average", '%.1f'%year_citation_list[3][1] + " citations on average", 
    	'%.1f'%year_citation_list[4][1] + " citations on average", '%.1f'%year_citation_list[5][1] + " citations on average", 
    	'%.1f'%year_citation_list[6][1] + " citations on average", '%.1f'%year_citation_list[7][1] + " citations on average", 
    	'%.1f'%year_citation_list[8][1] + " citations on average", '%.1f'%year_citation_list[9][1] + " citations on average", 
    	'%.1f'%year_citation_list[10][1] + " citations on average", '%.1f'%year_citation_list[11][1] + " citations on average" ],
    marker=dict(
        color='rgb(17,70,155)',
        line=dict(
            color='rgb(8,48,107)',
            width=1.0,
        )
    ),
)

	data = [trace0]
	layout = go.Layout(
	    title='Average Article Citations by Publication Year',
	)

	fig = go.Figure(data=data, layout=layout)
	py.plot(fig, filename='citations-by-year')



if __name__=="__main__":

### Invoke functions to gather data from APIs and populate database ###

	if len(sys.argv) > 1 and sys.argv[1] == '--rebuild':
		print('Gathering journal article citation data...')
		for subject in SUBJECT_LIST:
			articles = process_api_data(subject)
			ARTICLE_DICT.update(articles)

		print('Creating database articles.db...')
		create_db(DB_NAME)

		print('Populating database articles.db...')
		populate_db(DB_NAME)

	else:
		print('Using existing database.')


### Make it interactive ###
	
	def load_help_text():
	    with open('help.txt') as help:
	        return help.read()

	
	# function to let user choose data presentation options
	# input: nothing
	# return: nothing
	def choose_display_options():
		help = load_help_text()

		while True:
			user_input = input("Welcome! Enter a graph option, or enter 'help' for a list of possible data groupings: ")

			if user_input == 'help':
				print(help)
				continue

			elif user_input == 'exit':
				print('Goodbye!')
				return

			elif user_input == 'access':
				data = get_citations_by_access(DB_NAME)
				plot_access_citations(data)

			elif user_input == 'influence':
				data = get_influence_by_access(DB_NAME)
				plot_influential_citations(data)

			elif user_input == 'subject':
				data = create_subject_insts(DB_NAME)
				plot_citations_by_subject(data)

			elif user_input == 'year':
				data = get_citations_by_year(DB_NAME)
				plot_citations_by_year(data)

			elif user_input == 'list':
				article_insts = create_article_insts(DB_NAME)
				random_articles = random.choices(article_insts, k=25)
				for each in random_articles:
					print(each)
				print('\n')

			else:
				print("I'm sorry, I don't recognize that command. Please try another, or enter 'help' for options.")

	choose_display_options()



