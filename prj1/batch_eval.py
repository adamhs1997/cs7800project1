'''
a program for evaluating the quality of search algorithms using the vector model

it runs over all queries in query.text and get the top 10 results,
and then qrels.text is used to compute the NDCG metric

usage:
    python batch_eval.py index_file query.text qrels.text

    output is the average NDCG over all the queries

'''

from cranqry import loadCranQry
from random import choice
from query import QueryProcessor
from cran import CranFile
from index import InvertedIndex

# Values to set (using the init function)
n = 10

def eval():

    # Algorithm:
        # Pick N random samples from query.txt
        # Get top 10 results from bool query for each rnd query
        # Get top 10 results from vector query for each rnd query
        # Compute NDCG btn bool query results and qrels.txt
        # Compute NDCG btn vector query results and qrels.txt
        # Get p-value btn bool and vector
        
    # Get the query collection
    qc = loadCranQry(r"D:\CS 7800 Project 1\CranfieldDataset\query.text")
    poss_queries = list(qc)
    
    # Load up the inverted index
    ii = InvertedIndex()
    ii.load(r"D:\CS 7800 Project 1\prj1\iidx.pkl")
    
    # Load up the document collection
    cf = CranFile(r"..\CranfieldDataset\cran.all")
    
    # Get N random queries
    for _ in range(n):
        query = choice(poss_queries)
        
        # Initialize the query processor
        qp = QueryProcessor(query, ii, cf)
        
        # Run bool query
        bool_result = qp.booleanQuery()[:10]
        
        # Compensate for short lists with obviously "wrong" results
        while len(bool_result) < 10:
            bool_result.append(-1)
            
        # Run vector query
        vector_result = qp.vectorQuery(10)
        
        # Compensate for short lists with obviously "wrong" results
        while len(vector_result) < 10:
            vector_result.append(-1)

    print('Done')
    
def init():
    pass

if __name__ == '__main__':
    eval()
