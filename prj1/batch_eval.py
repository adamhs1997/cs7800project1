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
    
    # Get N random queries
    for _ in range(n):
        query = choice(poss_queries)
        print(query)

    print('Done')
    
def init():
    pass

if __name__ == '__main__':
    eval()
