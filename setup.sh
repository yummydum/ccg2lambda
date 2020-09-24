./en/download_dependencies.sh
mkdir data
mv en/sick* data/
mv en/SICK* data/
cp en/coqlib_sick.v coqlib.v
coqc coqlib.v
cp en/tactics_coq_sick.txt tactics_coq.txt
python run_depccg.py
mkdir data/subgoal_matched