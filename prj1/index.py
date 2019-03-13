

'''

Index structure:

    The Index class contains a list of IndexItems, stored in a dictionary type for easier access

    each IndexItem contains the term and a set of PostingItems

    each PostingItem contains a document ID and a list of positions that the term occurs

'''

import util
import doc
from cran import CranFile
from pickle import dump, load
from math import log10
from sys import argv


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
        
        # The number of times a term is in a document corresponds to 
        #   the length of the position list
        return len(self.positions)
       
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
        
        # We already have the postings in posting dict. Store the sorted docID keys
        #   in sorted_postings list, for easier reference in postings dict.
        self.sorted_postings = sorted(self.posting)
        
        # We sort the positions of each posting in place
        for doc in self.posting:
            self.posting[doc].sort()


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
            self.items[term].add(int(doc.docID), pos)


    def sort(self):
        ''' sort all posting lists by docID'''
        #ToDo
        
        # The actual sort is implemented in IndexItem. Just call it here.
        for item in self.items:
            self.items[item].sort()

    def find(self, term):
        return self.items[term] if term in self.items else None

    def save(self, filename):
        ''' save to disk'''
        # ToDo: using your preferred method to serialize/deserialize the index
        
        # Combine items dict and nDocs into a list so they can be pickled together
        to_pickle = [self.items, self.nDocs]
        
        # Use Pickle to dump the index to a file
        with open(filename, 'wb') as out:
            dump(to_pickle, out)

    def load(self, filename):
        ''' load from disk'''
        # ToDo
        
        # Load data back from pickled file
        with open(filename, 'rb') as inf:
            file_read = load(inf)
            self.items = file_read[0]
            self.nDocs = file_read[1]

    def idf(self, term):
        ''' compute the inverted document frequency for a given term'''
        #ToDo: return the IDF of the term
        
        # IDF of term t is log(total # of docs / # docs with t in it)
        return log10(self.nDocs / len(self.items[term].posting)) \
            if term in self.items else 0

    # more methods if needed


def test():
    ''' test your code thoroughly. put the testing cases here'''
    
    ####### TEST CASES FOR INVERTED INDEX CLASS #######
    
    # Get all documents from cran.all--let Cranfile object handle this
    cf = CranFile(r"..\CranfieldDataset\cran.all")
    
    # Build an inverted index object
    ii = InvertedIndex()
    
    # Index one document
    ii.indexDoc(cf.docs[0])
    
    # The first temr should be "experiment" (verified by printing contents of II)
    #   We want to ensure that find() finds it
    index_item = ii.find("experiment")
    print("Result of find:", index_item.term, index_item.posting)
    
    # Next, sort to ensure that it works
    # TODO: figure out what this should doc
    ii.sort()
    print("Sorted!")
    
    # Get the IDF of the term "experiment"
    #   Following the formula from our slides, this should be 0
    print("IDF:", ii.idf("experiment"))
    
    # Add back in the rest of Cranfield dataset
    for doc in cf.docs[1:]:
        ii.indexDoc(doc)
        
    # Re-do find now that we have more things in the index
    index_item = ii.find("experiment")
    print("Result of find:", index_item.term, index_item.posting)
    
    # Ensure sort works on larger index
    # Next, sort to ensure that it works
    # TODO: figure out what this should doc
    ii.sort()
    print("Sorted!")
    
    # Calculate IDF with larger index
    # Get the IDF of the term "experiment"
    #   Following the formula from our slides, this should be 0
    print("IDF:", ii.idf("experiment"))
    
    # Save off our index
    ii.save("index.pkl")
    
    # Read back in the index, ensure they are the same
    ii_from_file = InvertedIndex()
    ii_from_file.load("index.pkl")
    
    # Cannot determine if the actual items are equal objects, 
    #   so just ensure the stats are the same
    # print("Load matches saved items:", ii.items == ii_from_file.items)
    print("Load matches saved number of docs:", ii.nDocs == ii_from_file.nDocs)
    print("Load matches saved IDF for 'experiment':", 
        ii.idf("experiment") == ii_from_file.idf("experiment"))
    print("Load matches saved find term for 'experiment':",
        ii.find("experiment").term == ii_from_file.find("experiment").term)
    print("Load matches saved find posting for 'experiment':",
        str(ii.find("experiment").posting) == str(ii_from_file.find("experiment").posting))
         
    ####### TEST CASES FOR POSTING CLASS #######
    
    # Create test posting
    p = Posting(docID=1)
    
    # Test adding a position
    p.append(3)
    print("Position appended to posting:", p.positions == [3])
    
    # Add position out of order, ensure sort works
    p.append(1)
    print("Append is initially out-of-order:", p.positions == [3, 1])
    p.sort()
    print("Sort correctly sorts postings:", p.positions == [1, 3])
    
    # Ensure we can merge in new postings
    to_merge = [4, 5, 6]
    p.merge(to_merge)
    print("Merge correctly merges:", p.positions == [1, 3, 4, 5, 6])
    
    # Ensure term frequency is correctly
    print("Term frequency correctly counts postings:", p.term_freq() == 5)
    
    ####### TEST CASES FOR INDEX ITEM CLASS #######
    
    # Create index item
    iitem = IndexItem("abc")
    
    # Add value to index item
    iitem.add(0, 40)
    print("Document added to item:", 0 in iitem.posting)
    print("Posting created for document in item:", 
        type(iitem.posting[0]) == type(Posting(5)))
        
    ####### ADDITIONAL TEST CASES #######
    
    print("\nTHE FOLLOWING ARE BASED ON THE GIVEN TEST QUESTIONS")
    
    # Act on the assumption all words are stemmed
    #   This should be done in the tokenize part of util
    #   The idea was to re-stem all words and ensure they equal the words
    #     in the index, but some double-stemmings differ anyway.
    
    # Ensure stopwords were removed
    from nltk.stem.porter import PorterStemmer
    with open("stopwords") as f:
        stopwords = f.readlines()
    s = PorterStemmer()
    stopword_vector = list(
        map(lambda x: s.stem(x.strip()) in ii.items.items(), stopwords))
    print("All stopwords removed from index:", not any(stopword_vector))
    
    # Print number of terms in dict--Dr. Chen can ensure this is right
    print("Number of terms in dictionary:", len(ii.items))
    
    # Print average size of postings--Dr. Chen can ensure this makes sense
    sum = 0
    posting_count = 0
    for item in ii.items.values():
        for posting in item.posting.values():
            sum += len(posting.positions)
            posting_count += 1
    print("Average posting length:", sum/posting_count)
    

def indexingCranfield():
    #ToDo: indexing the Cranfield dataset and save the index to a file
    # command line usage: "python index.py cran.all index_file"
    # the index is saved to index_file
    
    # Ensure args are valid
    if len(argv) < 3:
        print("Syntax: python index.py <cran.all path> <index-save-location>")
        return

    # Grab arguments
    file_to_index = argv[1]
    save_location = argv[2]
    
    # Index file
    print("Indexing documents from", file_to_index + "...")
    cf = CranFile(file_to_index)
    ii = InvertedIndex()
    for doc in cf.docs:
        ii.indexDoc(doc)
        
    # Sort index before saving
    ii.sort()
        
    # Save off index
    ii.save(save_location)
    print("Index saved to", save_location + "!")
    

if __name__ == '__main__':
    test()  # Uncomment to run tests
    #indexingCranfield()
