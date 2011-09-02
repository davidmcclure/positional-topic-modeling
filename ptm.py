import re
import numpy as np

# Force numpy to not truncate arrays when printing them.
np.set_printoptions(threshold='nan')


class Splitter(object):

    '''
    Splits a text file into an ordered list of words.
    '''

    # List of punctuation characters to scrub. Omits, the single apostrophe,
    # which is handled separately so as to retain contractions.
    PUNCTUATION = ['(', ')', ':', ';', ',', '-', '!', '.', '?', '/', '"', '*']

    # Relative location of line-delimited list of stop words.
    STOP_WORD_PATH = 'stop_words.txt'

    # Carriage return strings, on *nix and windows.
    CARRIAGE_RETURNS = ['\n', '\r\n']

    # Final sanity-check regex to run on words before they get pushed onto the
    # core words list.
    WORD_REGEX = "^[a-z']+$"


    def __init__(self, filepath):
        '''
        Set source file location, build contractions list, initialize empty
        lists for lines and words, call split.
        '''
        self.filepath = filepath
        self.file = open(self.filepath)
        self.lines = []
        self.words = []
        self.stop_words = []
        self._load_stopwords()
        self.split()


    def _load_stopwords(self):
        '''
        Read list of stop words out of file.
        '''
        f = open(Splitter.STOP_WORD_PATH)
        for word in [line for line in f]:
            self.stop_words.append(self._clean_word(word, False))


    def split(self):
        '''
        Split file into an ordered list of words. Scrub out punctuation;
        lowercase everything; preserve contractions; disallow strings that
        include non-letters. En route, build a dictionary of {word: count}.
        '''
        self.lines = [line for line in self.file]
        self.word_counts_dictionary = {}
        for line in self.lines:
            words = line.split(' ')
            for word in words:
                clean_word = self._clean_word(word)
                if clean_word:
                    self.words.append(clean_word)
                    if word not in self.word_counts_dictionary:
                        self.word_counts_dictionary[word] = 1
                    else:
                        self.word_counts_dictionary[word] += 1


    def _clean_word(self, word, block_stop_words = True):
        '''
        Parses a space-delimited string from the text and determines whether or
        not it is a valid word. Scrubs punctuation, retains contraction
        apostrophes. If cleaned word passes final regex, returns the word;
        otherwise, returns None.
        '''
        word = word.lower()
        for punc in Splitter.PUNCTUATION + Splitter.CARRIAGE_RETURNS:
            word = word.replace(punc, '').strip("'")
        if not re.match(Splitter.WORD_REGEX, word): word = None
        if block_stop_words and word in self.stop_words: word = None
        return word



class Text(Splitter):

    '''
    An ordered series of words. Could be a single long text, or a series of
    texts strung together.
    '''


    def __init__(self, filepath):
        '''
        Set up the _called set, which keeps track of which functions have been
        called on the class. Used to manage dependencies among functions.
        '''
        Splitter.__init__(self, filepath)
        self._called = set()
        self._functions = {
            'build_unique_vocabulary': self.build_unique_vocabulary,
            'build_wordcounts_array': self.build_wordcounts_array
        }


    def _do_dependencies(self, dependencies):
        '''
        Executes a series of functions passed in as a list of strings.
        '''
        for function in dependencies:
            if function not in self._called: self._functions[function]()


    def build_unique_vocabulary(self):
        '''
        Construct a list of unique tokens, set number_of_uniques counter.
        '''
        self._called.add('build_unique_vocabulary')
        self.unique_vocabulary = []
        for word,count in self.word_counts_dictionary.iteritems():
            self.unique_vocabulary.append(word)
        self.number_of_uniques = len(self.unique_vocabulary)


    def build_wordcounts_array(self):
        '''
        Construct an array of structure [[word_id(int), wordcount(int)], .. ].
        '''
        self._called.add('build_wordcounts_array')
        self._do_dependencies(['build_unique_vocabulary'])
        self.word_counts_array = np.zeros([self.number_of_uniques, 1], dtype=int)
        for i,word in enumerate(self.unique_vocabulary):
            self.word_counts_array[i] = self.word_counts_dictionary[word]
