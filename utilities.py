# A collection of utilities. Used primarily by the comparers.


def __find_distance_to_nearest_neighbor(list_of_positions, position):
    '''
    Given a list of positions and a single position, find the distance between
    the position and its closest neighbor in the list.
    '''
    radii = []
    for i in list_of_positions:
       radii.append(abs(i-position))
    return min(radii)


def __avg(l):
    '''
    Average a list as an integer.
    '''
    return int(float(sum(l))/len(l))
