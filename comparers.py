# A library of comparer functions, each of which returns a integer coefficient
# that represents a metric that can be thought of as the "clumpiness" or "average
# radial distance" between the two word-position sets a and b.

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
