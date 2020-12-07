#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#  Copyright 2015 Pascual Martinez-Gomez
#  Copyright 2020 Riko Suzuki
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import pickle
import sys
import argparse
import codecs
import logging
from lxml import etree
import sys
from pathlib import Path
from tqdm import tqdm
import pandas as pd
from semantic_tools import prove_doc
from theorem import clean


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sem", type=Path)
    parser.add_argument("--abduction", type=str, choices=["naive", "spsa"])
    parser.add_argument("--timeout", type=int, default=100)
    parser.add_argument("--write", action="store_true", default=False)
    parser.add_argument("--bidirection", action="store_true", default=False)
    parser.add_argument("--gold_trees", action="store_true", default=True)
    parser.add_argument("--sick_all", action="store_true")
    parser.add_argument("--split")
    parser.add_argument("--test_run", action='store_true')
    args = parser.parse_args()
    args.subgoals = True

    logging.basicConfig(level=logging.WARNING)

    if not args.sem.exists():
        print(f'{args.sem} does not exist', file=sys.stderr)
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    # Load abduction
    if args.abduction is None:
        pass
    if args.abduction == "spsa":
        from abduction_spsa import AxiomsWordnet
        args.abduction = AxiomsWordnet()
    elif args.abduction == "naive":
        from abduction_naive import AxiomsWordnet
        args.abduction = AxiomsWordnet()

    if args.sick_all:
        stat = {}
        stat['pred'] = {}
        stat['goal_n'] = {}
        stat['readable_n'] = {}
        stat['errors'] = {}

        # Loop over the pairs
        count = 0
        files = sorted([f for f in args.sem.iterdir()])
        for f in tqdm(files):

            print(f)
            i = int(f.name.rstrip(".sem.xml").lstrip("pair_"))
            args.sem = f

            try:
                theorem = prove(args)
            except Exception as err:
                err = str(err)
                if err not in stat['erorrs']:
                    stat['errors'][err] = 0
                stat['erorrs'][err] += 1
                continue

            stat['pred'][i] = int(theorem.inference_result)
            stat['goal_n'][i] = len(theorem.subgoal)
            stat['readable_n'][i] = len(theorem.created_axioms)

            count += 1
            if args.test_run and count > 10:
                print(stat)
                break

        # save results
        if args.abduction:
            p = f'data/stat_abd.pkl'
        else:
            p = f'data/stat.pkl'

        with codecs.open(p, 'wb') as fout:
            pickle.dump(stat, fout)

    else:
        return prove(args)


def prove(args):
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(str(args.sem), parser)
    docs = root.findall('.//document')
    for doc in docs:

        theorem = prove_doc(doc, args.abduction, args)
        if theorem.theorems[0].inference_result:
            return theorem.theorems[0]

        # else preserve readable subgoal
        premise = clean(theorem.theorems[0].premises[0])
        hypothesis = clean(theorem.theorems[0].conclusion)
        created_axioms = theorem.theorems[0].created_axioms

        ab_output = str(args.sem).replace('parsed', 'subgoal_matched').replace(
            '.sem.xml', '.txt')
        with codecs.open(ab_output, 'w', 'utf-8') as fout:
            fout.write('Premise:\n')
            fout.write(premise + '\n\n')
            fout.write('Conclusion:\n')
            fout.write(hypothesis + '\n\n')
            fout.write('Subgoals:\n')
            for goal in theorem.theorems[0].subgoal:
                fout.write(goal + '\n')
            fout.write('\n')
            fout.write('Axioms:\n')
            for text in created_axioms:
                fout.write(text + '\n')

        if created_axioms:
            p = Path(f'data/generated_axioms_{args.split}.csv')
            p2 = Path(f'data/expected_label_{args.split}.csv')

            if args.abduction:
                p = f'data/generated_axioms_{args.split}_abd.csv'
                p2 = Path(f'data/expected_label_{args.split}_abd.csv')
            else:
                p = f'data/generated_axioms_{args.split}.csv'
                p2 = Path(f'data/expected_label_{args.split}.csv')

            # init when start
            b = (args.split == 'train') and (args.sem == 'pair_1.sem.xml')
            b2 = (args.split == 'test') and (args.sem == 'pair_101.sem.xml')
            if b or b2:
                p.unlink()
                p2.unlink()

            with codecs.open(p, 'a', 'utf-8') as fout:
                premise = ' '.join(theorem.theorems[0].original)
                hypothesis = ' '.join(theorem.theorems[0].original2)
                fout.write(args.sem.name + '\n')
                fout.write(premise + '\n')
                fout.write(hypothesis + '\n')
                fout.write('Axioms:\n')
                for text in created_axioms:
                    fout.write(text + '\n')
                fout.write(
                    '\n==================================================\n')

    return theorem.theorems[0]


if __name__ == '__main__':
    main()
