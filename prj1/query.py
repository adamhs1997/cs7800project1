
'''
query processing

'''

from norvig_spell import correction
from index import InvertedIndex, IndexItem, Posting
from cran import CranFile
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
        
        # Get preprocessed query
        clean_query = self.preprocessing()
        
        # Basic algo:
            # Retrieve postings for each term in query
            # Intersect postings lists
            
        # Get posting for first term to start the list
        stop_pos = 0
        for idx, word in enumerate(clean_query):
            # Skip over any missing stopword positions
            if word == '': continue
            
            stop_pos = idx + 1
            master_postings = self.index.find(word).sorted_postings
            
            # Negate if our first position is a not
            # NOTE: We don't have to check for or yet, as this isn't a valid first word
            if idx-1 in not_positions:
                print("Negate!", word)
                master_postings = [n for n in list(range(1, self.index.nDocs+1))
                    if n not in master_postings]
                    
            break
            
        # Get postings for rest of query terms
        for idx, word in enumerate(clean_query[stop_pos:]):
            # Skip any empty stopword positions
            if word == '': continue
            
            # Get the containing index item
            index_item = self.index.find(word)
            
            # Get docs where the word is posted
            current_postings = index_item.sorted_postings
            
            # Negate if last position is a not
            if stop_pos+idx-1 in not_positions:
                print("Negate!", word)
                current_postings = [n for n in list(range(1, self.index.nDocs+1))
                    if n not in current_postings]
            
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



def test():
    ''' test your code thoroughly. put the testing cases here'''
    
    # Grab index file to restore II
    ii = InvertedIndex()
    ii.load(r"D:\CS 7800 Project 1\prj1\iidx.pkl")
    
    # Get the document collection
    cf = CranFile(r"..\CranfieldDataset\cran.all")
    
    # Initialize a query processor
    qp = QueryProcessor("slipstream diameter", ii, cf)
    print(qp.booleanQuery())
    

def query():
    ''' the main query processing program, using QueryProcessor'''

    # ToDo: the commandline usage: "echo query_string | python query.py index_file processing_algorithm"
    # processing_algorithm: 0 for booleanQuery and 1 for vectorQuery
    # for booleanQuery, the program will print the total number of documents and the list of docuement IDs
    # for vectorQuery, the program will output the top 3 most similar documents


if __name__ == '__main__':
    test()
    query()
