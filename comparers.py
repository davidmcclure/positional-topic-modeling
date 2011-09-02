# A library of comparer functions, each of which performs the core task of
# figuring out whether a positions list b should be considered "clumped" with
# position list a. There are many different ways of doing this, each of which
# reflects different assumptions and intuitions about how to identify
# meaningful correlations.

import utilities as ut

def _CMP_closest_neighbor_average_distance(a, b):
    '''
    For each position in b, walk a find the closest neighbor in b. At the
    end, average these radii and return True if the average is less than
    the supplied threshold.
    '''
    radii = []
    for i in b:
        radii.append(ut.__find_distance_to_nearest_neighbor(a, i))
    return ut.__avg(radii)
