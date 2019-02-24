
'''
   utility functions for processing terms

    shared by both indexing and query processing
'''

from nltk.stem.porter import PorterStemmer

### Initialization code that we only want to do once ###
# Read in stop words
stop_words = open(r'D:\CS 7800 Project 1\prj1\stopwords').read()

# Initialize a stemmer object
stemmer = PorterStemmer()


def isStopWord(word):
    ''' using the NLTK functions, return true/false'''
    return word in stop_words

def stemming(word):
    ''' return the stem, using a NLTK stemmer. check the project description for installing and using it'''
    return stemmer.stem(word)

def tokenize_doc(doc):
    """ Get each token (split on whitespace); lowercase each token """
    return list(map(lambda word: word.lower(), doc.split()))
