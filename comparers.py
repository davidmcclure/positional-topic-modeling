# A library of comparer functions, each of which returns a integer coefficient
# that represents a metric that can be thought of as the "clumpiness" or "average
# radial distance" between the two word-position sets a and b.

def _CMP_closest_neighbor_average_distance(a, b):
    '''
    For each position in b, walk a to find the closest neighbor in b and cache
    the radial distance. Return the average of the radii.
    '''
    radii = []
    for b_index in b:
        per_index_radii = []
        for a_index in a:
            per_index_radii.append(abs(a_index-b_index))
        radii.append(min(per_index_radii))
    return int(float(sum(radii))/len(radii))
