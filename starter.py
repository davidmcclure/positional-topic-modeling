import ptm
wp = ptm.Text('texts/war_and_peace.txt')
wp.build_positions_list()

for i,p in enumerate(wp.positions[:100]):
    print wp.unique_vocab[wp.subset_vocab_i[i]]
    print p
