prove:
	python scripts/prove.py sentences.sem.xml --proof sentence.proofs --subgoals --subgoals_out sentence.subgoals 

sick:
	download
	cp en/coqlib_sick.v coqlib.v
	coqc coqlib.v
	cp en/tactics_coq_sick.txt tactics_coq.txt
