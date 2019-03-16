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
from index import InvertedIndex, IndexItem, Posting
from metrics import ndcg_score
from scipy.stats import wilcoxon, ttest_ind
from sys import argv

# Values to set (using the init function)
n = 10
index_file = ""
query_path = ""
qrels_path = ""

def eval():

    # Algorithm:
        # Pick N random samples from query.txt
        # Get top 10 results from bool query for each rnd query
        # Get top 10 results from vector query for each rnd query
        # Compute NDCG btn bool query results and qrels.txt
        # Compute NDCG btn vector query results and qrels.txt
        # Get p-value btn bool and vector
        
    # Get the query collection
    qc = loadCranQry(query_path)
    poss_queries = list(qc)
    
    # Load up the inverted index
    ii = InvertedIndex()
    ii.load(index_file)
    
    # Load up the document collection
    cf = CranFile("cran.all")
    
    # Get ground-truth results from qrels.txt
    with open(qrels_path) as f:
        qrels = f.readlines()
        
    # Index qrels into a dict
    qrel_dict = {}
    for qrel in qrels:
        qrel_split = qrel.split()
        if int(qrel_split[0]) in qrel_dict:
            qrel_dict[int(qrel_split[0])].append(int(qrel_split[1]))
        else:
            qrel_dict[int(qrel_split[0])] = [int(qrel_split[1])]
    
    # Run over N random queries, collecting NDCGs
    bool_ndcgs = []
    vector_ndcgs = []
    for _ in range(n):
        # Get random query ID
        query_id = choice(poss_queries)
        
        # Get the query
        if 0 < int(query_id) < 10:
            query_id = '00' + str(int(query_id))
        elif 9 < int(query_id) < 100:
            query_id = '0' + str(int(query_id))
        try: 
            query = qc[query_id].text
        except KeyError:
            print("Invalid query id", query_id)
            return
            
        # Initialize the query processor
        qp = QueryProcessor(query, ii, cf)
        
        # Run bool query
        bool_result = qp.booleanQuery()[:10]
            
        # Run vector query
        vector_result = qp.vectorQuery(10)
            
        # Pull top 10 ground-truth results from qrels dict
        gt_results = qrel_dict[poss_queries.index(query_id)+1][:10]
        
        # Fill rest of ground-truth list with "wrong" 0s if necessary
        while len(gt_results) < 10:
            gt_results.append(0)
            
        # Compute NDCG for bool query
        bool_ndcg = ndcg_score(gt_results, bool_result)
        
        # Compute NDCG for vector query
        vector_ndcg = ndcg_score(gt_results, vector_result)
        
        # Accumulate NDCGs
        bool_ndcgs.append(bool_ndcg)
        vector_ndcgs.append(vector_ndcg)
        
    # Average out score lists
    bool_avg = 0
    for bool in bool_ndcgs:
        bool_avg += bool
    bool_avg /= len(bool_ndcgs)
    
    vector_avg = 0
    for vector in vector_ndcgs:
        vector_avg += vector
    vector_avg /= len(vector_ndcgs)
    
    # Present averages and p-values
    print("Boolean NDCG average:", bool_avg)
    print("Vector NDCG average:", vector_avg)
    if n > 9:
        print("Wilcoxon p-value:", wilcoxon(bool_ndcgs, vector_ndcgs).pvalue)
    else:
        print("Wilcoxon p-value: Sample size too small to be significant")
    print("T-Test p-value:", ttest_ind(bool_ndcgs, vector_ndcgs).pvalue)
    
def init():
    global n
    global index_file
    global query_path
    global qrels_path
    
    # Ensure args are valid
    if len(argv) is not 5:
        print("Syntax: python batch_eval.py <index-file-loc> <query-loc> <qrels-loc> <n>")
        return False

    # Grab arguments
    index_file = argv[1]
    query_path = argv[2]
    qrels_path = argv[3]
    n = int(argv[4])
    
    # Ensure we have enough test cases
    if n < 2:
        print("N value is too small. Try again.")
        return False
    
    return True

if __name__ == '__main__':
    if init():
        eval()
