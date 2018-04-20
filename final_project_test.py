# You must create at least 3 test cases and use at least 15 assertions or calls to ‘fail( )’
import unittest
from final_project import *

# Tests to show program can access data from all sources
class TestAPICalls(unittest.TestCase):

	def test_springer_search(self):
		spring1 = get_springer_data('Education')
		spring2 = get_springer_data('Chemistry')

		self.assertEqual(spring1['result'][0]['recordsDisplayed'], '50')
		self.assertEqual(spring2['result'][0]['recordsDisplayed'], '50')

	def test_plos_search(self):
		plos1 = get_plos_data('Education')
		plos2 = get_plos_data('Chemistry')

		self.assertEqual(len(plos1['response']['docs']), 50)
		self.assertEqual(len(plos2['response']['docs']), 50)

	def test_semantic_scholar_search(self):
		springer_impact = get_impact_data('10.1007/s11121-016-0635-6')
		plos_impact = get_impact_data('10.1371/journal.pgen.1002625')
		
		self.assertGreater(len(springer_impact['citations']), 6)
		self.assertGreater(len(plos_impact['citations']), 30)


# Tests to show database is correctly constructed and can satisfy necessary queries
class TestDatabase(unittest.TestCase):

	def test_subject_table(self):
		conn = sqlite3.connect(DB_NAME)
		cur = conn.cursor()
		statement = "SELECT Subject FROM Subjects"
		results = cur.execute(statement).fetchall()

		self.assertEqual(len(results), 10)
		self.assertEqual(results[2][0], 'Nutrition')

		conn.close()


	def test_query(self):
		conn = sqlite3.connect(DB_NAME)
		cur = conn.cursor()
		statement = """SELECT C.AccessLevel, AVG(A.CitationCount)
						FROM Articles as A
							JOIN AccessLevels as C
							ON A.AccessLevelId = C.Id
						GROUP BY C.AccessLevel 
						"""
		results = cur.execute(statement).fetchall()

		self.assertEqual(len(results), 2)
		self.assertEqual(results[1][0], 'Subscription Required')
		self.assertGreater(results[0][1], 0.1)

		conn.close()


	def test_foreign_key_relation(self):
		conn = sqlite3.connect(DB_NAME)
		cur = conn.cursor()
		statement = "SELECT * FROM Articles LIMIT 1"
		results = cur.execute(statement).fetchall()
		columns = cur.description

		self.assertEqual(columns[6][0], 'SubjectId')
		self.assertEqual(type(results[0][6]), int)

		conn.close()


# Tests to show data processing functions and structures support the program's presentation options
class TestDataProcessing(unittest.TestCase):
	
	def test_processing_functions(self):		
		infl = get_influence_by_access(DB_NAME)
		subj = create_subject_insts(DB_NAME)
		year = get_citations_by_year(DB_NAME)
		arti = create_article_insts(DB_NAME)

		self.assertEqual(type(infl), list)
		self.assertEqual(type(infl[0]), tuple)
		
		self.assertEqual(type(subj), list)
		self.assertEqual(len(subj), 10)
		self.assertEqual(subj[5].subject, 'Immunology')

		self.assertEqual(type(year), list)
		self.assertEqual(len(year[1]), 2)

		self.assertEqual(type(arti), list)
		self.assertEqual(type(arti[0].citations), int)


# test that plotly opens
class TestGraphs(unittest.TestCase):

	def test_plotly_functions(self):
		infl = get_influence_by_access(DB_NAME)
		subj = create_subject_insts(DB_NAME)
		try:
			plot_influential_citations(infl)
			plot_citations_by_subject(subj)
		except:
			self.fail()


if __name__ == '__main__':
    unittest.main()