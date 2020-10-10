prove:
	python scripts/prove.py data/parsed/pair_${n}.sem.xml  --write --abduction spsa 
	
prove_all:
	python scripts/prove.py data/parsed  --write --abduction spsa --sick_all
