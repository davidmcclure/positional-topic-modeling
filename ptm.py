import re
import numpy as np
import time
import memoized as mem
import comparers
import pickle
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

    # Default comparer to use.
    DEF_COMPARER = '_CMP_closest_neighbor_average_distance'

    # Default parameterizer to use.
    DEF_PARAMETERIZER = '_PARAM_number_of_words_to_hit_1000'

    # Directory to save and read pickles.
    PICKLES_DIR = 'pickles/'

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
        # ** prep
        self.build_unique_vocab()
        # ** /prep
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
        # ** prep
        self.build_unique_vocab()
        self.build_wordcounts_array()
        # ** /prep
        self.subset_vocab_i = []
        min_count = int((self.total_wordcount * float(numerator)) / denominator)
        for i,count in enumerate(self.word_counts_array):
            if count >= min_count and self.unique_vocab[i] not in self.stop_words:
                self.subset_vocab_i.append(i)
        self.subset_count = len(self.subset_vocab_i)


    @mem.memoized
    def build_subset_text_word_positions(self):
        '''
        Build a list of tuples of structure (id,position) in which the id is an
        index in subset_vocab_i and the position is the ordered position of the
        word in the text.
        '''
        # ** prep
        self.build_unique_vocab()
        self.build_wordcounts_array()
        self.build_subset_vocab(Text.DEF_NUMERATOR, Text.DEF_DENOMINATOR)
        # ** /prep
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
        # ** prep
        self.build_unique_vocab()
        self.build_wordcounts_array()
        self.build_subset_vocab(Text.DEF_NUMERATOR, Text.DEF_DENOMINATOR)
        self.build_subset_text_word_positions()
        # ** /prep
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
        # ** prep
        self.build_unique_vocab()
        self.build_wordcounts_array()
        self.build_subset_vocab(Text.DEF_NUMERATOR, Text.DEF_DENOMINATOR)
        self.build_subset_text_word_positions()
        self.build_positions_list()
        # ** /prep
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
        # ** prep
        self.build_unique_vocab()
        self.build_wordcounts_array()
        self.build_subset_vocab(Text.DEF_NUMERATOR, Text.DEF_DENOMINATOR)
        self.build_subset_text_word_positions()
        self.build_positions_list()
        # ** /prep
        scores = [] # tuple of (word_id, score)
        word_positions = self.get_positions_by_word(word)
        for j,i in enumerate(self.subset_vocab_i):
            other_word_positions = self.positions[j]
            score = getattr(comparers, Text.DEF_COMPARER)(word_positions, other_word_positions)
            scores.append((self.unique_vocab[i], score))
        scores = sorted(scores, key=itemgetter(1))
        if truncate: scores = scores[:truncate]
        return scores


    def build_positional_similarity_stack_for_subset_id(self, index, truncate=None):
        '''
        For the provided subset_id index, run through each of the other words and call the
        specified comparer function. Then, sort the list ascending.
        '''
        # ** prep
        self.build_unique_vocab()
        self.build_wordcounts_array()
        self.build_subset_vocab(Text.DEF_NUMERATOR, Text.DEF_DENOMINATOR)
        self.build_subset_text_word_positions()
        self.build_positions_list()
        # ** /prep
        scores = [] # tuple of (word_id, score)
        word_positions = self.positions[index]
        for j,i in enumerate(self.subset_vocab_i):
            other_word_positions = self.positions[j]
            score = getattr(comparers, Text.DEF_COMPARER)(word_positions, other_word_positions)
            scores.append((i, score))
        scores = sorted(scores, key=itemgetter(1))
        if truncate: scores = scores[:truncate]
        return scores


    def build_positional_similarity_stacks_for_all_words(self):
        '''
        Build position similarity stacks for all words.
        '''
        # ** prep
        self.build_unique_vocab()
        self.build_wordcounts_array()
        self.build_subset_vocab(Text.DEF_NUMERATOR, Text.DEF_DENOMINATOR)
        self.build_subset_text_word_positions()
        self.build_positions_list()
        # ** /prep
        self.positional_similarity_stacks = []
        for i,word in enumerate(self.subset_vocab_i):
            stack = self.build_positional_similarity_stack_for_subset_id(i)
            self.positional_similarity_stacks.append(stack)


    def _pickle_similarity_stacks(self):
        '''
        Pickle the similarity stacks.
        '''
        # ** prep
        self.build_unique_vocab()
        self.build_wordcounts_array()
        self.build_subset_vocab(Text.DEF_NUMERATOR, Text.DEF_DENOMINATOR)
        self.build_subset_text_word_positions()
        self.build_positions_list()
        self.build_positional_similarity_stacks_for_all_words()
        # ** /prep
        filename = Text.DEF_COMPARER + '_' + str(int(time.time())) + '.pkl'
        output = open(Text.PICKLES_DIR + filename, 'wb')
        pickle.dump(self.positional_similarity_stacks)
        output.close()


    def _unpickle_similarity_stacks(self, filename):
        '''
        Load pickled similarity stacks.
        '''
        f = open(Text.PICKLES_DIR + filename, 'rb')
        self.positional_similarity_stacks = pickle.load(f)


    def _positions_id_to_word(self, positions_id):
        '''
        Given the id of a list of positions, return the id of the word that the
        positions correspond to from unique_vocab.
        '''
        return self.unique_vocab[self.subset_vocab_i[positions_id]]


    def build_unconsolidated_topic_clumps(self, radius):
        '''
        For each set of word positions, iterate over the other positions; if a
        word pair has a distance metric of under the given radius, break the
        pair off into a group and consolidate their position indecides into a
        single list; then remove the clumped words from the list of free
        agents. For each successive word, test against existing topic clumps
        first, then against remaining free agent words. If a word gets run
        across all clumps and free agents and never yields a distance score
        under the radius threshold, throw it out.

        Clumps are tuples with this structure:

        ([list of unique_vocab indecies of words in clump], [composite
        positions list])
        '''
        # ** prep
        self.build_unique_vocab()
        self.build_wordcounts_array()
        self.build_subset_vocab(Text.DEF_NUMERATOR, Text.DEF_DENOMINATOR)
        self.build_subset_text_word_positions()
        self.build_positions_list()
        # ** /prep

        clumps = []
        free_agents = []

        for i,positions in enumerate(self.positions):
            free_agents.append([i,positions, True])

        for i,positions in enumerate(self.positions):
            clumped = False
            for clump in clumps:
                score = getattr(comparers, Text.DEF_COMPARER)(positions, clump[1])
                if score < radius:
                    test_word = self._positions_id_to_word(i)
                    clump[1] += positions
                    clump[1].sort()
                    clump[0].append(test_word)
                    clumped = True
                    break

            if not clumped:
                for free_agent in free_agents:
                    if free_agent[0] != i and free_agent[2]:
                        score = getattr(comparers, Text.DEF_COMPARER)(positions, free_agent[1])
                        if score < radius:
                            free_agent_word = self._positions_id_to_word(free_agent[0])
                            test_word = self._positions_id_to_word(i)
                            composite_indices = free_agent[1] + positions
                            composite_indices.sort()
                            new_clump = [[free_agent_word, test_word], composite_indices]
                            clumps.append(new_clump)
                            free_agent[2] = False
                            break

            print str(i) + ' / ' + str(len(self.positions))

        return clumps
