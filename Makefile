prove:
	python scripts/prove.py data/parsed/pair_${n}.sem.xml  --subgoals --subgoals_out data/subgoal_matched/pair_${n}.txt --abduction spsa 
	
