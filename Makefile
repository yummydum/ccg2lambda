prove:
	python scripts/prove.py data/parsed/pair_${n}.sem.xml

prove_abd:
	python scripts/prove.py data/parsed/pair_${n}.sem.xml --abduction spsa

prove_test:
	python scripts/prove.py data/parsed_test/pair_${n}.sem.xml  

prove_all:
	python scripts/prove.py data/parsed  --abduction spsa --sick_all --split train

prove_all_test:
	python scripts/prove.py data/parsed_test  --sick_all --split test

prove_all_test_abduction:
	python scripts/prove.py data/parsed_test   --abduction spsa --sick_all --split test

test:
	pytest scripts/test_prove.py -s -vv