# Experiments on SICK at NAACL-HLT 2018

First, you need to clone the repository and checkout a different branch at first:
```bash
git clone https://github.com/verypluming/ccg2lambda
git checkout naacl
```

Then, ensure that you have downloaded [C&C parser](http://www.cl.cam.ac.uk/~sc609/candc-1.00.html),
[EasyCCG parser](https://github.com/mikelewis0/easyccg), and [depccg parser](https://github.com/masashi-y/depccg) and wrote their installation locations
in the files `en/parser_location.txt`.
```bash
cat en/parser_location.txt
candc:/home/usr/software/candc/candc-1.00
easyccg:/home/usr/software/easyccg
depccg:/home/usr/software/depccg
```

Second, you need to download the [SICK dataset](http://alt.qcri.org/semeval2014/task1/index.php?id=data-and-tools)
by running the following script:

```bash
./en/download_dependencies.sh
```

Also, you need to download phrase axioms extracted from training dataset from [Here](https://github.com/verypluming/ccg2lambda/releases/download/naaclhlt2018/sick_phrase.sqlite3). 
After that, put `sick_phrase.sqlite3` into the top directory.

You can evaluate the end-to-end system performance of a certain list of semantic templates on
the test split of SICK by doing:

```bash
./en/phraseexp_eval.sh 10 test en/semantic_templates_en_event.yaml
```

This script will coordinate the tokenization, syntactic parsing (with C&C and
EasyCCG), semantic parsing and theorem proving (with Coq) using 10 processes.
Syntactic and semantic parsing results will be written in `parsed` directory.
Entailment judgements and an HTML graphical representation of semantic
composition (and constructed theorem) will be written in `results` directory.
You can see a summary of performance by doing:

```bash
cat phrase_results/score.txt
```

and you should see something similar to this:

```
Correct parsing: 0.9847 (4852/4927)
Accuracy: 0.8422 (4150/4927)
Recall: 0.7722
Precision: 0.8408
F1 score: 0.8048
Gold_correct_total: 2134
System_answer_total: 1960
System_correct_total: 1648
----------------------------------------------------------------
                            system                              
     |        |     yes |      no | unknown |   error |   total 
----------------------------------------------------------------
     |     yes|    1082 |       3 |     318 |      11 |    1414 
gold |      no|      18 |     566 |     118 |      18 |     720 
     | unknown|     247 |      44 |    2456 |      46 |    2793 
     |   total|    1347 |     613 |    2892 |      75 |    4927 
----------------------------------------------------------------
```

If you want to see the results (syntactic/semantic parses, entailment judgements and HTML
visualizations) but do not wish to run the software, you can uncompress the file
`en/sick_intermediate_results.tgz` by doing:

```bash
tar xvzf en/sick_intermediate_results.tgz
```

which will create the `plain/`, `parsed/` and `phrase_results/` directories.
