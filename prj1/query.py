
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
        print(self.raw_query)
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
            print("word", word)
            print("curlist", master_postings)
            # Skip any empty stopword positions
            if word == '': continue
            
            # Merge in any existing postings
            if type(word) is type([]):
                print("list")
                # If a not query
                if idx-1 in not_positions:
                    print("Negate!", word)
                    word = [n for n in list(range(1, self.index.nDocs+1))
                        if n not in word]
            
                # If master_postings empty or this is an or query
                if first_word or idx-1 in or_positions:
                    master_postings.extend(word)
                    master_postings = sorted(master_postings)
                    first_word = False
                    continue
                    
                # Otherwise, just merge the posting lists
                master_postings = [posting for posting in word
                    if posting in master_postings]
                print(3)
                
                continue
            
            # Get the containing index item
            index_item = self.index.find(word)
            
            # Get docs where the word is posted
            if index_item:
                current_postings = index_item.sorted_postings
            else: current_postings = []
            
            # If an or query, just append current to master
            if idx-1 in or_positions:
                master_postings.extend(current_postings)
                master_postings = sorted(master_postings)
                continue
            
            # Negate if last position is a not
            if idx-1 in not_positions:
                print("Negate!", word)
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
                
            print(word)
            print(master_postings)
            
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
        # TODO: Move into index construction?
        tfidf_dict = {}
        for doc in doc_dict:
            word_vector = []
            for word in self.index.items:
                # Get tf
                try:
                    tf = self.index.find(word).posting[doc].term_freq()
                except KeyError: # if not in doc
                    tf = 0
                
                # Get idf
                idf = self.index.idf(word)
                
                # Calculate tf-idf; add to current dict
                word_vector.append(log10(1 + tf) * idf)
                
            # Normalize the word vector
            accum = 0
            for word in word_vector:
                accum += word**2
                
            accum = sqrt(accum)
                
            for idx, word in enumerate(word_vector):
                word_vector[idx] /= accum
                
            tfidf_dict[doc] = word_vector
                
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


def test():
    ''' test your code thoroughly. put the testing cases here'''
    
    # Grab index file to restore II
    ii = InvertedIndex()
    ii.load(r"D:\CS 7800 Project 1\prj1\iidx.pkl")
    
    # Get the document collection
    cf = CranFile(r"..\CranfieldDataset\cran.all")
    
    # Initialize a query processor
    qp = QueryProcessor("what effect do thermal stresses have on the compressive buckling strength of ring-stiffened cylinders", ii, cf)
    print(qp.booleanQuery())
    
    #print(qp.vectorQuery(k=10))
    

def query():
    ''' the main query processing program, using QueryProcessor'''

    # ToDo: the commandline usage: "echo query_string | python query.py index_file processing_algorithm"
    # processing_algorithm: 0 for booleanQuery and 1 for vectorQuery
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
    cf = CranFile(r"..\CranfieldDataset\cran.all")
    
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
        print(qp.vectorQuery(k=3))
    else:
        print("Invalid processing algorithm", processing_algo +
            ". Use 0 (boolean) or 1 (vector).")


if __name__ == '__main__':
    test()
    #query()
