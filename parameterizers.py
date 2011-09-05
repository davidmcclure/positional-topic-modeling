# A set of functions that do calculations on a provided positional similarity
# stack. Used as callback methods for sorted() calls that order the full
# similarity stacks. These methods always take a single similarity stack (s)
# return a single, integer metric that can be compared against all the others.
# The input s always takes the form of a list of tuples of structure (word,
# distance metric). When iterating over s, always slice at [1:] to scrub out
# the identity listing at the top of the stack.

import utilities as ut

def _PARAM_number_of_words_to_hit_1000(s):
    '''
    Count the number of words in the stack that it takes for the distance
    metric to hit 1000.
    '''
    for i,stack_word in enumerate(s[1:]):
        if stack_word[1] >= 1000:
            return i
            break
