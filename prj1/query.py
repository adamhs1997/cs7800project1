
'''
query processing

'''

from norvig_spell import correction
from index import InvertedIndex, IndexItem, Posting
from cran import CranFile
from cranqry import loadCranQry
from math import log10, sqrt
from collections import Counter
from sys import argv
import util

class QueryProcessor:

    def __init__(self, query, index, collection):
        ''' index is the inverted index; collection is the document collection'''
        self.raw_query = query
        self.index = index
        self.docs = collection

    def preprocessing(self):
        ''' apply the same preprocessing steps used by indexing,
            also use the provided spelling corrector. Note that
            spelling corrector should be applied before stopword
            removal and stemming (why?)'''

        #ToDo: return a list of terms
        
        # Tokenize and lowercase doc into list form
        token_list = util.tokenize_doc(self.raw_query)
            
        # Helper function to replace stopwords with empty string
        def remove_stop_word(tok):
            return "" if util.isStopWord(tok) else tok
            
        # Correct spelling of each word
        tokens_corrected_spell = list(map(lambda tok: correction(tok),
            token_list))
            
        # Remove the stopwords from both positional list and token list
        token_list_no_stopword = list(map(remove_stop_word, 
            tokens_corrected_spell))
        
        # Stem the words
        stemmed_token_list = list(map(lambda tok: util.stemming(tok),token_list_no_stopword))
        
        return stemmed_token_list


    def booleanQuery(self):
        ''' boolean query processing; note that a query like "A B C" is transformed to "A AND B AND C" for retrieving posting lists and merge them'''
        #ToDo: return a list of docIDs
        
        # Ref: https://nlp.stanford.edu/IR-book/html/htmledition/processing-boolean-queries-1.html
        
        # Parse position of OR and NOT
        #   We must do this before stopwords removed
        or_list = list(map(lambda t: t.lower() == "or", self.raw_query.split()))
        or_positions = []
        for idx, bool in enumerate(or_list):
            if bool: or_positions.append(idx)
            
        not_list = list(map(lambda t: t.lower() == "not", self.raw_query.split()))
        not_positions = []
        for idx, bool in enumerate(not_list):
            if bool: not_positions.append(idx)
        
        # Parse out parenthesis positions
        open_paren_list = list(map(lambda t: '(' in t, self.raw_query.split()))
        close_paren_list = list(map(lambda t: ')' in t, self.raw_query.split()))
        if len(open_paren_list) is not len(close_paren_list):
            print("Error: Parenthesis mismatch.")
            return
        open_paren_positions = []
        close_paren_positions = []
        for idx, bool in enumerate(open_paren_list):
            if bool: open_paren_positions.append(idx)
        for idx, bool in enumerate(close_paren_list):
            if bool: close_paren_positions.append(idx)
        
        # Get preprocessed query
        clean_query = self.preprocessing()
            
        # Handle precedence of parens
        for idx, pos in enumerate(open_paren_positions):
            # Get the actual subquery within parens
            subquery = clean_query[open_paren_positions[idx] : close_paren_positions[idx]+1]
            
            # Run bool query on subquery
            subquery_result = self.bool_query_helper(subquery, not_positions, or_positions)
            
            # Replace subquery with completed postings
            clean_query[open_paren_positions[idx]] = subquery_result
            
            # Replace rest of subquery with empty strings (will be skipped)
            for i, w in enumerate(clean_query[open_paren_positions[idx]+1 : close_paren_positions[idx]+1]):
                clean_query[i+open_paren_positions[idx]+1] = ''
                
        # Process the remainder of the query
        answer = self.bool_query_helper(clean_query, not_positions, or_positions)
            
        return answer
        
        
    def bool_query_helper(self, query, not_positions, or_positions):
        # Mark whether this is the first word in the query
        first_word = True
        
        # Get posting for first term to start the list
        master_postings = []
        
        # Get postings for rest of query terms
        for idx, word in enumerate(query):
            # Skip any empty stopword positions
            if word == '': continue
            
            # Merge in any existing postings
            if type(word) is type([]):
                # If a not query
                if idx-1 in not_positions:
                    word = [n for n in list(range(1, self.index.nDocs+1))
                        if n not in word]
            
                # If master_postings empty or this is an or query
                if first_word or idx-1 in or_positions:
                    master_postings.extend(word)
                    master_postings = sorted(list(set(master_postings)))
                    first_word = False
                    continue
                    
                # Otherwise, just merge the posting lists
                master_postings = [posting for posting in word
                    if posting in master_postings]
                
                continue
            
            # Get the containing index item
            index_item = self.index.find(word)
            
            # Get docs where the word is posted
            if index_item:
                current_postings = index_item.sorted_postings[:]
            else: current_postings = []
            
            # If an or query, just append current to master
            if idx-1 in or_positions:
                master_postings.extend(current_postings)
                master_postings = sorted(list(set(master_postings)))
                continue
            
            # Negate if last position is a not
            if idx-1 in not_positions:
                current_postings = [n for n in list(range(1, self.index.nDocs+1))
                    if n not in current_postings]
                    
            # Handle case where this is the first thing in the list
            if first_word:
                master_postings = current_postings
                first_word = False
                continue
            
            # Merge the current postings into master postings
            master_postings = [posting for posting in current_postings
                if posting in master_postings]
            
        return master_postings


    def vectorQuery(self, k):
        ''' vector query processing, using the cosine similarity. '''
        #ToDo: return top k pairs of (docID, similarity), ranked by their cosine similarity with the query in the descending order
        # You can use term frequency or TFIDF to construct the vectors
        
        # May need to let x% of words match here to get any matches
        #   (do same for bool)
        
        # For each term in query...
            # Grab the tf-idf for each word in each doc
            # Hold on to all doc ids that contain (most?) words in query
            # Compute cosine sim and rank results
            
        # Get preprocessed query
        clean_query = self.preprocessing()
        
        # Get IndexItems for each term in the query
        #   Hold on to these in a list so we make sure each term in doc
        
        # Hold on to the number of times each word appears in a doc
        doc_dict = {}
        for word in clean_query:
            # Skip any empty stopword positions
            if word == '': continue
            
            # Add in the docs
            word_lookup = self.index.find(word)
            if word_lookup is None: continue
            
            for doc in word_lookup.posting:
                if doc not in doc_dict:
                    doc_dict[doc] = 1
                else: doc_dict[doc] += 1
            
        # Compute the vector representation for each doc, using tf-idf for
        #   EVERY possible word
        # --> This is pre-computed in the inverted index
        tfidf_dict = self.index.doc_tfidf
                
        # Compute the cosine score between each doc and the query
        # Ref: https://nlp.stanford.edu/IR-book/html/htmledition/computing-vector-scores-1.html
        scores = {}
        word_count_query = Counter(clean_query)
        for word in clean_query:
            # Skip any empty stopword positions
            if word == '': continue
        
            # Get word tf-idf
            tf = word_count_query[word]
            idf = self.index.idf(word)
            tfidf = log10(1+tf) * idf
            
            # Count up the scores for doc weights
            word_lookup = self.index.find(word)
            if word_lookup is None: continue
            
            for doc in doc_dict:
                # Get the posting for the word
                cur_posting = word_lookup.posting
                
                # Calculate the score
                if doc not in cur_posting:
                    score = 0
                else:
                    score = tfidf * cur_posting[doc].term_freq()
                
                # Add up the scores
                if doc in scores:
                    scores[doc] += score
                else:
                    scores[doc] = score
                    
        # Normalize scores by doc length
        for doc in scores:
            scores[doc] /= len(self.docs.docs[doc-1].body.split())
            
        # Sort the scores by score
        sorted_scores = sorted(scores.items(), reverse=True, key=lambda x: x[1])

        # Return top k scores
        return sorted_scores[:k]


def test(index_loc, cran_loc, qrels_loc):
    ''' test your code thoroughly. put the testing cases here'''
    
    ##### SETUP ITEMS #####
    
    # Grab index file to restore II
    ii = InvertedIndex()
    ii.load(index_loc)
    
    # Get the document collection
    cf = CranFile(cran_loc)
    
    # Get ground-truth results from qrels.txt
    with open(qrels_loc) as f:
        qrels = f.readlines()
        
    # Index qrels into a dict
    qrel_dict = {}
    for qrel in qrels:
        qrel_split = qrel.split()
        if int(qrel_split[0]) in qrel_dict:
            qrel_dict[int(qrel_split[0])].append(int(qrel_split[1]))
        else:
            qrel_dict[int(qrel_split[0])] = [int(qrel_split[1])]
            
    ##### INITIAL TEST ITEMS #####
    print("TESTS BASED ON SUGGESTED TESTING POINTS")
    
    # Ensure tf is correct
    #   Find a random word and check TF value against what is manually done
    posting_list = ii.find("experiment").posting
    tf_vector = []
    for posting in posting_list:
        tf_vector.append(len(posting_list[posting].positions) \
            == posting_list[posting].term_freq())
    print("TF is computed correctly:", all(tf_vector))
    
    # Ensure idf is correct
    print("IDF is computed correctly:", log10(ii.nDocs / len(posting_list)) \
        == ii.idf("experiment"))
        
    # As both tf and idf are correct, and tf-idf is a product of the two,
    #   it is reasonable to assume tf-idf is computed correctly
            
    ##### BOOL QUERY TESTS #####
    
    # Here, I use very specific boolean queries to ensure that a 
    #   limited number of documents are returned
    print("\nBOOL QUERY TESTS")
    
    # Ensure that the exact title of doc 8 matches for doc 8 
    doc8 = "measurements of the effect of two-dimensional and three-dimensional roughness elements on boundary layer transition"
    qp1 = QueryProcessor(doc8, ii, cf)
    print("Bool query matches on exact title:", qp1.booleanQuery() == [8])
    
    # Ensure that bool query matches very specific AND query
    qp2 = QueryProcessor("hugoniot and infinitesimally", ii, cf)
    print("Bool query matches on specific AND query ('hugoniot and infinitesimally'):", qp2.booleanQuery() == [329])
    
    # Test that an OR query is handled properly
    #   Both gravel and stagnation have completely distinct postings lists.
    #   OR should merge them.
    gravel_postings = ii.find("gravel").sorted_postings[:]
    stag_postings = ii.find("stagnat").sorted_postings[:]
    gravel_postings.extend(stag_postings)
    qp3 = QueryProcessor("gravel or stagnation", ii, cf)
    print("Bool query successfully handles OR ('gravel or stagnation'):", 
        qp3.booleanQuery() == sorted(gravel_postings))
    
    # Test that NOT is handled properly
    #   The posting list for "diameter" is a subset of "slipstream" postings
    #   (oddly enough). To test this works, do "slipstream and not diameter"
    #   and we chould get slipstream's postings minus those of diameter.
    slip_postings = ii.find("slipstream").sorted_postings[:]
    diam_postings = ii.find("diamet").sorted_postings[:]
    slip_not_diam = [t for t in slip_postings if t not in diam_postings]
    print("Bool query successfully handles NOT ('slipstream and not diameter'):", 
        QueryProcessor("slipstream and not diameter", ii, cf).booleanQuery() \
          == slip_not_diam)
          
    # Ensure AND/OR order doesn't matter
    print("Bool query can handle query regardless of AND order ('a and b' = 'b and a'):",
        QueryProcessor("slipstream and diameter", ii, cf).booleanQuery() \
          == QueryProcessor("diameter and slipstream", ii, cf).booleanQuery())
    print("Bool query can handle query regardless of OR order ('a or b' = 'b or a'):",
        QueryProcessor("slipstream or diameter", ii, cf).booleanQuery() \
          == QueryProcessor("diameter or slipstream", ii, cf).booleanQuery())
          
    # Ensure that the presence of parens does not change query results
    print("Bool query can handle query regardless of parens ('slipstream and diameter'):",
        QueryProcessor("slipstream and diameter", ii, cf).booleanQuery() \
          == QueryProcessor("(slipstream and diameter)", ii, cf).booleanQuery())
          
    # Ensure parentheses do not change order of processing for AND-AND and OR-OR queries
    print("Bool query AND is accociative ('(a and b) and c' = 'a and (b and c)'):",
        QueryProcessor("(slipstream and diameter) and thrust", ii, cf).booleanQuery() \
          == QueryProcessor("slipstream and (diameter and thrust)", ii, cf).booleanQuery())
    print("Bool query OR is accociative ('(a or b) or c' = 'a or (b or c)'):",
        QueryProcessor("(slipstream or diameter) or thrust", ii, cf).booleanQuery() \
          == QueryProcessor("slipstream or (diameter or thrust)", ii, cf).booleanQuery())
          
    # Ensure parentheses properly group items
    #   Tested by doing the query "manually" by adding/orring the correct terms
    part_one = QueryProcessor("conduction and cylinder and gas", ii, cf).booleanQuery()
    part_two = QueryProcessor("radiation and gas", ii, cf).booleanQuery()
    part_one.extend(part_two)
    expected_result = QueryProcessor("hugoniot", ii, cf).booleanQuery()
    expected_result.extend(part_one)
    print("Bool query parens successfully group conflicting operators:", 
        QueryProcessor("(conduction and cylinder and gas) or (radiation and gas) or hugoniot", ii, cf).booleanQuery() \
          == sorted(list(set(expected_result))))
          
    ##### VECTOR QUERY TESTS #####
    
    # For this, just ensure that most of the results are in the expected list
    print("\nVECTOR QUERY TESTS")
    
    # Ensure vector query can match on exact title
    print("Vector query matches on exact title:", qp1.vectorQuery(1) == [8])
    
    # Try a few example queries from query.text
    #   As long as one-fifth of t-10 are in gt_result, call it a pass
    # Note that queries with larger answer sets were chosen to
    #   ensure there were enough to get to one-fifth of ten
    qc = loadCranQry("query.text")
    poss_queries = list(qc)
    
    # Query 001
    result = QueryProcessor(qc["001"].text, ii, cf).vectorQuery(10)
    gt_result = qrel_dict[poss_queries.index("001")+1]
    correct_vector = list(map(lambda x: x in gt_result, result))
    print("Vector query is at least one-fifth correct for query 001:", sum(
        correct_vector) > 2)
        
    # Query 128
    result = QueryProcessor(qc["128"].text, ii, cf).vectorQuery(10)
    gt_result = qrel_dict[poss_queries.index("128")+1]
    correct_vector = list(map(lambda x: x in gt_result, result))
    print("Vector query is at least one-fifth correct for query 128:", sum(
        correct_vector) > 2)
        
    # Query 226
    result = QueryProcessor(qc["226"].text, ii, cf).vectorQuery(10)
    gt_result = qrel_dict[poss_queries.index("226")+1]
    correct_vector = list(map(lambda x: x in gt_result, result))
    print("Vector query is at least one-fifth correct for query 226:", sum(
        correct_vector) > 2)
        
    # Query 196
    result = QueryProcessor(qc["196"].text, ii, cf).vectorQuery(10)
    gt_result = qrel_dict[poss_queries.index("196")+1]
    correct_vector = list(map(lambda x: x in gt_result, result))
    print("Vector query is at least one-fifth correct for query 196:", sum(
        correct_vector) > 2)
        
    # Query 291
    result = QueryProcessor(qc["291"].text, ii, cf).vectorQuery(10)
    gt_result = qrel_dict[poss_queries.index("291")+1]
    correct_vector = list(map(lambda x: x in gt_result, result))
    print("Vector query is at least one-fifth correct for query 291:", sum(
        correct_vector) > 2)

def query():
    ''' the main query processing program, using QueryProcessor'''

    # ToDo: the commandline usage: "echo query_string | python query.py index_file processing_algorithm"
    # processing_algorithm: 0 for booleanQuery and 1 for vectorQuer
    # for booleanQuery, the program will print the total number of documents and the list of docuement IDs
    # for vectorQuery, the program will output the top 3 most similar documents
    
    # Ensure args are valid
    if len(argv) is not 5:
        print("Syntax: python query.py <index-file-path> <processing-algorithm> <query.txt path> <query-id>")
        return

    # Grab arguments
    index_file_loc = argv[1]
    processing_algo = argv[2]
    query_file_path = argv[3]
    query_id = argv[4]
    
    # Grab index file to restore II
    ii = InvertedIndex()
    ii.load(index_file_loc)
    
    # Get the document collection
    cf = CranFile("cran.all")
    
    # Get the query collection
    qc = loadCranQry(query_file_path)
    
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
    
    # Initialize a query processor
    qp = QueryProcessor(query, ii, cf)
    
    # Do query
    if int(processing_algo) is 0:
        print(qp.booleanQuery())
    elif int(processing_algo) is 1:
        result = qp.vectorQuery(k=3)
        for r in result:
            print("Doc", r[0], "Score", r[1])
    else:
        print("Invalid processing algorithm", processing_algo +
            ". Use 0 (boolean) or 1 (vector).")


if __name__ == '__main__':
    #test("TEST.pkl", "cran.all", "qrels.text")
    query()
