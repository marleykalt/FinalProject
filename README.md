# FinalProject
Final Project for SI 507 at the University of Michigan School of Information
This project compares article-level metrics for scholarly publications, using Plotly to present graphs visualizing the data.

There are three sections to this document: Data Sources, Code Structure and User Guide.


DATA SOURCES

This program gathers data from three sources: Springer Meta API, PLOS Search API and Semantic Scholar API.

Springer Meta API:
This API is used to access metadata for articles published in Springer scientific journals. This program collects basic bibliographic information from the Springer Meta API, including an article’s title, author, publication date, journal, access level (denoted in the database as either “open access” or “subscription required”), and digital object identifier (DOI). More information can be found here: https://dev.springernature.com/docs . An API key is required for access, which can be obtained here: https://dev.springernature.com/signup .

PLOS Search API:
This API is used to access metadata for articles published in PLOS Open Access journals. This program collects basic bibliographic information from the PLOS Search API, including an article’s title, author, publication date, journal, access level (which will always be open access), and DOI. More information can be found here: http://api.plos.org/solr/ . An API key is required for access, which can be obtained here: http://api.plos.org/registration/ .

Semantic Scholar API:
This API is used to obtain citation data about a specific article, using the article’s DOI as an identifier. The program gathers the overall citation count and the number of influential citations (‘influential citations’ is a metric determined by Semantic Scholar) for each article. More information can be found here: https://api.semanticscholar.org/ . No API key is required.

To incorporate these keys into the program, users should create a file in the same directory, named ‘secrets.py’. This file only needs two lines of code, to assign the value of each API key to a variable (‘springer_key’ and ‘plos_key’). It should look like this, with your own API key inserted between the quotation marks:

springer_key = “<your api key here>”

plos_key = “<your api key here>”


To run this program, users should install all of the modules listed in the requirements.txt file. In addition, Plotly requires users to have an account and an API key. More information on how to use Plotly can be found here: https://plot.ly/python/getting-started/ .


CODE STRUCTURE

I have written the program to:
	1. Define functions that make calls to each of the APIs and define classes
	2. Invoke those functions and store the data in a database
	3. Query the database to support four different data comparisons (includes creating lists and class instances)
	4. Plot the data using Plotly. Presentation options can be chosen through user input in the command line (further explained 
	below)

The main data processing function is named ‘process_api_data’. It is defined in lines 143-193. This function takes a string as input, which should be the subject term used to search Springer and PLOS articles. It invokes smaller functions to fetch and cache data from each of the three APIs. It returns a dictionary in which each key is a DOI (unique identifier) for an article. The value for each DOI is a dictionary that contains the article metadata that is relevant to the program: title, author, date, journal, subject, publisher, access level, citation count and influential citation count.

Other important data processing functions are ‘get_citations_by_access’ (lines 298-311), ‘get_influence_by_access’ (lines 316-329) and ‘get_citations_by_year’ (lines 334-345). These take the database name as input and query the database based on certain parameters for data comparison. Each function returns a list which is used to plot the data using Plotly.

The functions ‘create_subject_insts’ (lines 350-373) and ‘create_article_insts’ (lines 379-401) also take the database name as input, but return a list of Subject class instances (defined in lines 115-123) and Article class instances (defined in lines 125-134), respectively. Instances of the Subject class support graphing data by subject groups. Instances of the Article class support showing a randomized list of articles from the database, so users can better understand the data without having to look at the database itself.

There is also a large dictionary that helps organize data, assigned to the global variable ARTICLE_DICT. This dictionary is created from invoking the ‘process_api_data’ function for each subject term. It contains all of the relevant data returned from the three APIs and is used to populate the database.


USER GUIDE
The program should be run in the user’s command line. There is an optional command line argument, ‘—-rebuild’, that allows users to fetch new data (or will use cached data, if available) and rebuild the database.

After the database is rebuilt, or if this optional argument is not used, the program will prompt the user for input. There are seven input strings that the program will recognize. Four of them (‘access’, ‘influence’, ‘subject’, ‘year’) will create Plotly graphs showing different data comparisons. One input (‘list’) will print to the console the string representation of 25 randomized Article class instances. The full explanations of each possible input string are as follows:

‘access’: Shows the average number of citations for articles, based on whether they are open access or subscription-based.

‘influence’: Shows the average number of influential citations for articles, based on whether they are open access or subscription-based.

‘subject’: Shows the average number of citations for articles from each of the 10 subjects.

‘year’: Shows the average number of citations for articles from different publication years.

‘list’: Prints a list of 25 random articles from the database.

‘help’: Allows you to understand all data presentation options.

‘exit’: Exits the program.



