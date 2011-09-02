import ptm

wp = ptm.Text('texts/war_and_peace.txt')
wp.build_wordcounts_array()

print wp.word_counts_array
