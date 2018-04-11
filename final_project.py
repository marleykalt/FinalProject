# import statements - need to be pip installed in virtual env
import requests
import json
from secrets import *

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
# return: a list of DOIs for articles retrieved from Springer
def get_springer_data(search_subject):
	springer_doi_list = []

	baseurl = 'http://api.springer.com/meta/v1/json?'
	params = {}
	params['api_key'] = springer_key # api key is required; imported from secrets.py
	params['q'] = ['subject:' + search_subject, 'country:"United States"', 'type:Journal'] # defines the query to be performed - many options, case sensitive
	params['p'] = 25 # requests should return 25 results

	unique_ident = params_unique_combination(baseurl, params)
	#print(unique_ident)

	if unique_ident in CACHE_DICTION:
		for article in CACHE_DICTION[unique_ident]['records']:
			doi = article['identifier']
			springer_doi_list.append(doi[4:]) # need to strip off 'doi:' from each result
		return springer_doi_list
	else:
		resp = requests.get(baseurl, params)
		CACHE_DICTION[unique_ident] = json.loads(resp.text)
		dumped_json_cache = json.dumps(CACHE_DICTION)
		fw = open(CACHE_FNAME,"w")
		fw.write(dumped_json_cache)
		fw.close()

		for article in CACHE_DICTION[unique_ident]['records']:
			doi = article['identifier']
			springer_doi_list.append(doi[4:])
		return springer_doi_list
# return value has a 'records displayed' field that could be good for determining if the result is okay
# may only be able to use one-word subject terms (worked: Mathematics, Chemistry, Psychology, Education)
# has an openaccess parameter that is true / false
# may be able to get subject terms for database from the restatement of the query that's returned in the results


# x = get_springer_data('Mathematics')
# print(x)

# function to make a request to the PLOS Search API, and cache data
# input: a subject term to search
# return: a list of DOIs articles retrieved from PLOS
def get_plos_data(search_subject):
	plos_doi_list = []

	baseurl = 'http://api.plos.org/search'
	params = {}
	params['api_key'] = plos_key # api key is required; imported from secrets.py
	params['q'] ='subject:' + search_subject
	params['rows'] = 25
	params['wt'] = 'json'

	unique_ident = params_unique_combination(baseurl, params)
	#print(unique_ident)

	if unique_ident in CACHE_DICTION:
		for article in CACHE_DICTION[unique_ident]['response']['docs']:
			doi = article['id']
			plos_doi_list.append(doi)
		return plos_doi_list	
	else:
		resp = requests.get(baseurl, params)
		CACHE_DICTION[unique_ident] = json.loads(resp.text)
		dumped_json_cache = json.dumps(CACHE_DICTION)
		fw = open(CACHE_FNAME,"w")
		fw.write(dumped_json_cache)
		fw.close()
		for article in CACHE_DICTION[unique_ident]['response']['docs']:
			doi = article['id']
			plos_doi_list.append(doi)
		return plos_doi_list

# x = get_plos_data('Education')
# print(x)


# function to make a request to the Altmetric API, and cache data
# input: a doi from a specific article
# return: python dictionary with article-level metrics for that doi
def get_altmetric_data(doi):
	pass


### Store API data in database ###

# DB setup: takes data from the cache dictionary

def create_db(dbname):
	pass

# function to create and populate a database
# input:
# return:
def populate_db(dbname):
	pass


### Present data ###

# plotly functions
# may also need functions to process data - create dictionaries for each data presentation option from the database, to draw from for plotly


### Make it interactive ###

# input:
# return:
# what this function does:
# - get user input to decide which subjects to search (provide suggestions)
# - create a database
# - let user choose data presentation options
def interactive_commands():
	pass



