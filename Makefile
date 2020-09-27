prove:
	python scripts/prove.py data/parsed/pair_${n}.sem.xml  --subgoals --abduction spsa 
	
prove_all:
	python scripts/prove.py data/parsed  --subgoals --abduction spsa --sick_all
