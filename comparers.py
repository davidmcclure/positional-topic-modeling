# A library of comparer functions, each of which returns a integer coefficient
# that represents a metric that can be thought of as the "clumpiness" or "average
# radial distance" between the two word-position sets a and b.

import utilities as ut

def _CMP_closest_neighbor_average_distance(a, b):
    '''
    For each position in b, walk a to find the closest neighbor in b and cache
    the radial distance. Return the average of the radii.
    '''
    radii = []
    for i in b:
        sub_radii = []
        for j in a:
            sub_radii.append(abs(j-i))
        radii.append(min(sub_radii))
    return ut.__avg(radii)
