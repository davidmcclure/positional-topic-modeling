import ptm
p = ptm.Text('texts/paradise_lost.txt')
clumps = p.build_unconsolidated_topic_clumps(2000)
