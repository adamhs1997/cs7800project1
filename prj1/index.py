

'''

Index structure:

    The Index class contains a list of IndexItems, stored in a dictionary type for easier access

    each IndexItem contains the term and a set of PostingItems

    each PostingItem contains a document ID and a list of positions that the term occurs

'''

import util
import doc
from cran import CranFile


class Posting:
    def __init__(self, docID):
        self.docID = docID
        self.positions = []

    def append(self, pos):
        self.positions.append(pos)

    def sort(self):
        ''' sort positions'''
        self.positions.sort()

    def merge(self, positions):
        self.positions.extend(positions)

    def term_freq(self):
        ''' return the term frequency in the document'''
        #ToDo
       
    # For testing purposes...
    def __repr__(self):
        return str(self.positions)


class IndexItem:
    def __init__(self, term):
        self.term = term
        self.posting = {} #postings are stored in a python dict for easier index building
        self.sorted_postings= [] # may sort them by docID for easier query processing

    def add(self, docid, pos):
        ''' add a posting'''
        if not docid in self.posting:
            self.posting[docid] = Posting(docid)
        self.posting[docid].append(pos)

    def sort(self):
        ''' sort by document ID for more efficient merging. For each document also sort the positions'''
        # ToDo


class InvertedIndex:

    def __init__(self):
        self.items = {} # list of IndexItems
        self.nDocs = 0  # the number of indexed documents


    def indexDoc(self, doc): # indexing a Document object
        ''' indexing a docuemnt, using the simple SPIMI algorithm, but no need to store blocks due to the small collection we are handling. Using save/load the whole index instead'''
        
        # Using the SPIMI algorithm as defined at
        # https://nlp.stanford.edu/IR-book/html/htmledition/single-pass-in-memory-indexing-1.html
        
        # Each term in a doc has its own index item!!!
        
        # Preprocess first...
        # Call tokenize_doc to convert doc title and body into tokenized list, in lowercase
        # Do remove stopwords and stemming as expected

        # ToDo: indexing only title and body; use some functions defined in util.py
        # (1) convert to lower cases,
        # (2) remove stopwords,
        # (3) stemming
        
        # Then go term-by-term and create the index. Use algorithm to track which terms already in index, add new ones if not. If we create a new index item, add it to the self.items dict!!!
        
        # ---
        
        # Increment number of documents indexed
        self.nDocs += 1
        
        # Grab title and body of doc, merge into one string
        doc_string = doc.title + " " + doc.body
        
        # Tokenize and lowercase doc into list form
        token_list = util.tokenize_doc(doc_string)
            
        # Helper function to replace stopwords with empty string
        def remove_stop_word(tok):
            return "" if util.isStopWord(tok) else tok
            
        # Remove the stopwords from both positional list and token list
        token_list_no_stopword = list(map(remove_stop_word, token_list))
        
        # Stem the words
        stemmed_token_list = list(map(lambda tok: util.stemming(tok), token_list_no_stopword))
        
        # Note that the stemmed tokens are now our terms
        for pos, term in enumerate(stemmed_token_list):
            # Skip over stopwords, now replaced by ""
            if term == "": continue
            
            # If this term has already appeared, update the existing posting
            if not term in self.items:
                self.items[term] = IndexItem(term)
            self.items[term].add(doc.docID, pos)


    def sort(self):
        ''' sort all posting lists by docID'''
        #ToDo

    def find(self, term):
        return self.items[term]

    def save(self, filename):
        ''' save to disk'''
        # ToDo: using your preferred method to serialize/deserialize the index

    def load(self, filename):
        ''' load from disk'''
        # ToDo

    def idf(self, term):
        ''' compute the inverted document frequency for a given term'''
        #ToDo: return the IDF of the term

    # more methods if needed


def test():
    ''' test your code thoroughly. put the testing cases here'''
    cf = CranFile (r"..\CranfieldDataset\cran.all")
    
    # print(cf.docs[0].body)
    ii = InvertedIndex()
    for doc in cf.docs:
        ii.indexDoc(doc)
    
    print("Done!")
    # Test out the thing
    for item in ii.items.values():
        print(item.term, item.posting)
    print ('Pass')

def indexingCranfield():
    #ToDo: indexing the Cranfield dataset and save the index to a file
    # command line usage: "python index.py cran.all index_file"
    # the index is saved to index_file

    print ('Done')

if __name__ == '__main__':
    test()
    indexingCranfield()
