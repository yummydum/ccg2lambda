prove:
	python scripts/prove.py data/parsed/pair_${n}.sem.xml

prove_save_rs:
	python scripts/prove.py data/parsed/pair_${n}.sem.xml --save_readable_subgoal

prove_save_rs_all:
	python scripts/prove.py data/parsed --sick_all --save_readable_subgoal

prove_use_rs:
	python scripts/prove.py data/parsed/pair_${n}.sem.xml --use_readable_subgoal

prove_use_rs_all:
	python scripts/prove.py data/parsed --sick_all --use_readable_subgoal

prove_abd:
	python scripts/prove.py data/parsed/pair_${n}.sem.xml --abduction spsa

prove_test:
	python scripts/prove.py data/parsed_test/pair_${n}.sem.xml  

prove_all:
	python scripts/prove.py data/parsed --sick_all --split train

prove_all_test:
	python scripts/prove.py data/parsed_test  --sick_all --split test

prove_all_test_abduction:
	python scripts/prove.py data/parsed_test   --abduction spsa --sick_all --split test

test:
	pytest scripts/test_prove.py -s -vv