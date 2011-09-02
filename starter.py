import ptm
wp = ptm.Text('texts/war_and_peace.txt')
wp.build_positions_list()

for i,p in enumerate(wp.positions[:100]):
    print wp.unique_vocab[i]
    print p
