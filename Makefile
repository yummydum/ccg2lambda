prove:
	python scripts/prove.py data/parsed/pair_${n}.sem.xml  --write  
	
prove_all:
	python scripts/prove.py data/parsed  --write --abduction spsa --sick_all

prove_all_test:
	python scripts/prove.py data/parsed_test  --write  --sick_all

prove_all_test_abduction:
	python scripts/prove.py data/parsed_test  --write  --abduction spsa --sick_all

test:
	pytest scripts/test_prove.py -s -vv