import re
import numpy as np
import memoized as mem
import comparers
from operator import itemgetter

# Force numpy to not truncate arrays when printing them.
np.set_printoptions(threshold='nan')


class Splitter(object):

    '''
    Splits a text file into an ordered list of words.
    '''

    # List of punctuation characters to scrub. Omits, the single apostrophe,
    # which is handled separately so as to retain contractions.
    PUNCTUATION = ['(', ')', ':', ';', ',', '-', '!', '.', '?', '/', '"', '*', "'"]

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
            self.stop_words.append(self._clean_word(word))


    def _clean_word(self, word):
        '''
        Parses a space-delimited string from the text and determines whether or
        not it is a valid word. Scrubs punctuation, retains contraction
        apostrophes. If cleaned word passes final regex, returns the word;
        otherwise, returns None.
        '''
        word = word.lower()
        for punc in Splitter.PUNCTUATION + Splitter.CARRIAGE_RETURNS:
            word = word.replace(punc, '')
        if not re.match(Splitter.WORD_REGEX, word): word = None
        return word


    def split(self):
        '''
        Split file into an ordered list of words. Scrub out punctuation;
        lowercase everything; preserve contractions; disallow strings that
        include non-letters. En route, build a dictionary of {word: count}.
        '''
        self.lines = [line for line in self.file]
        self.word_counts_dictionary = {}
        self.total_wordcount = 0
        for line in self.lines:
            words = line.split(' ')
            for word in words:
                self.total_wordcount += 1
                clean_word = self._clean_word(word)
                if clean_word:
                    self.words.append(clean_word)
                    try: self.word_counts_dictionary[clean_word] += 1
                    except KeyError: self.word_counts_dictionary[clean_word] = 1



class Text(Splitter):

    '''
    An ordered series of words. Could be a single long text, or a series of
    texts strung together.
    '''

    # Defaults for the ratio to use when deciding whether or not a word is to
    # infrequent to include in the subset vocabulary.
    DEF_NUMERATOR = 5
    DEF_DENOMINATOR = 100000

    # Default comparer to user.
    DEF_COMPARER = '_CMP_closest_neighbor_average_distance'

    @mem.memoized
    def build_unique_vocab(self):
        '''
        Construct a list of unique tokens, set number_of_uniques counter.
        '''
        self.unique_vocab = []
        self.word_index_dictionary = {}
        for word,count in self.word_counts_dictionary.iteritems():
            self.unique_vocab.append(word)
        self.number_of_uniques = len(self.unique_vocab)
        for i, word in enumerate(self.unique_vocab):
            self.word_index_dictionary[word] = i


    @mem.memoized
    def build_wordcounts_array(self):
        '''
        Construct an array of structure [[word_id(int), wordcount(int)], .. ].
        '''
        self.build_unique_vocab()
        self.word_counts_array = np.zeros([self.number_of_uniques, 1], dtype=int)
        for i,word in enumerate(self.unique_vocab):
            self.word_counts_array[i] = self.word_counts_dictionary[word]


    @mem.memoized
    def build_subset_vocab(self, numerator, denominator):
        '''
        Build a subset of the unique vocabulary to consider when modeling
        topics. Eliminiate stop words and words with counts that do not cross
        the numerator/denominator threshold.
        '''
        self.build_unique_vocab()
        self.build_wordcounts_array()
        self.subset_vocab_i = []
        min_count = int((self.total_wordcount * float(numerator)) / denominator)
        for i,count in enumerate(self.word_counts_array):
            if count >= min_count and self.unique_vocab[i] not in self.stop_words:
                self.subset_vocab_i.append(i)


    @mem.memoized
    def build_subset_text_word_positions(self):
        '''
        Build a list of tuples of structure (id,position) in which the id is an
        index in subset_vocab_i and the position is the ordered position of the
        word in the text.
        '''
        self.build_unique_vocab()
        self.build_wordcounts_array()
        self.build_subset_vocab(Text.DEF_NUMERATOR, Text.DEF_DENOMINATOR)
        self.subset_text_word_positions = []
        for i,word in enumerate(self.words):
            word_index = self.word_index_dictionary[word]
            if word_index in self.subset_vocab_i:
                self.subset_text_word_positions.append((word_index, i))


    @mem.memoized
    def build_positions_list(self):
        '''
        Build a list of structure list[i] = [x,y,z,...], where i is the index
        of the word in subset_vocab_i and x,y,z,... are the positions of each
        instance of the word in the text.
        '''
        self.build_unique_vocab()
        self.build_wordcounts_array()
        self.build_subset_vocab(Text.DEF_NUMERATOR, Text.DEF_DENOMINATOR)
        self.build_subset_text_word_positions()
        self.positions = []
        for i in self.subset_vocab_i:
            w_positions = []
            for id_pos in self.subset_text_word_positions:
                if id_pos[0] == i: w_positions.append(id_pos[1])
            self.positions.append(w_positions)


    def get_positions_by_word(self, word):
        '''
        Return positions list for a word. Return None if word is not present in
        the subset vocabulary.
        '''
        self.build_unique_vocab()
        self.build_wordcounts_array()
        self.build_subset_vocab(Text.DEF_NUMERATOR, Text.DEF_DENOMINATOR)
        self.build_subset_text_word_positions()
        self.build_positions_list()
        try:
            unique_index = self.word_index_dictionary[word]
            subset_index = self.subset_vocab_i.index(unique_index)
            return self.positions[subset_index]
        except KeyError:
            return None


    # console helper
    def build_positional_similarity_stack_for_word(self, word, truncate=None):
        '''
        For the provided word, run through each of the other words and call the
        specified comparer function. Then, sort the list ascending.
        '''
        self.build_unique_vocab()
        self.build_wordcounts_array()
        self.build_subset_vocab(Text.DEF_NUMERATOR, Text.DEF_DENOMINATOR)
        self.build_subset_text_word_positions()
        self.build_positions_list()
        scores = [] # tuple of (word_id, score)
        word_positions = self.get_positions_by_word(word)
        for j,i in enumerate(self.subset_vocab_i):
            other_word_positions = self.positions[j]
            score = getattr(comparers, Text.DEF_COMPARER)(word_positions, other_word_positions)
            scores.append([self.unique_vocab[i], score])
        scores = sorted(scores, key=itemgetter(1))
        if truncate: scores = scores[:truncate]
        return scores

