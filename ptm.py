import re
import numpy as np


class Splitter(object):

    '''
    Splits a text file into an ordered list of words.
    '''

    # List of punctuation characters to scrub. Omits, the single apostrophe,
    # which is handled separately so as to retain contractions.
    PUNCTUATION = ['(', ')', ':', ';', ',', '-', '!', '.', '?', '/', '"', '*']

    # Carriage return strings, on *nix and windows.
    CARRIAGE_RETURNS = ['\n', '\r\n']

    # Final sanity-check regex to run on words before they get
    # pushed onto the core words list.
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
        self.split()


    def split(self):
        '''
        Split file into an ordered list of words. Scrub out punctuation;
        lowercase everything; preserve contractions; disallow strings that
        include non-letters.
        '''
        self.lines = [line for line in self.file]
        for line in self.lines:
            words = line.split(' ')
            for word in words:
                clean_word = self._clean_word(word)
                if clean_word:
                    self.words.append(clean_word)


    def _clean_word(self, word):
        '''
        Parses a space-delimited string from the text and determines whether or
        not it is a valid word. Scrubs punctuation, retains contraction
        apostrophes. If cleaned word passes final regex, returns the word;
        otherwise, returns None.
        '''
        word = word.lower()
        for punc in Splitter.PUNCTUATION + Splitter.CARRIAGE_RETURNS:
            word = word.replace(punc, '').strip("'")
        return word if re.match(Splitter.WORD_REGEX, word) else None


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
        _set = set()
        for word in self.words:
            _set.add(word)
        self.unique_vocabulary = list(_set)
        self.number_of_uniques = len(self.unique_vocabulary)

    def build_wordcounts_array(self):
        '''
        Construct an array of structure [[word_id(int), wordcount(int)], .. ].
        '''
        self._called.add('build_wordcounts_array')
        self._do_dependencies(['build_unique_vocabulary'])
        print self.number_of_uniques
