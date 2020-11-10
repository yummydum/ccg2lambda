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

import sys
import argparse
import codecs
import logging
from lxml import etree
from subprocess import TimeoutExpired
import sys
import textwrap
from pathlib import Path
from tqdm import tqdm
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
    args = parser.parse_args()
    args.subgoals = True

    logging.basicConfig(level=logging.WARNING)

    if not args.sem.exists():
        print(f'{args.sem} does not exist', file=sys.stderr)
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    if args.abduction is None:
        pass
    if args.abduction == "spsa":
        from abduction_spsa import AxiomsWordnet
        args.abduction = AxiomsWordnet()
    elif args.abduction == "naive":
        from abduction_naive import AxiomsWordnet
        args.abduction = AxiomsWordnet()

    if args.sick_all:
        errors = 0
        for f in tqdm(sorted(list(args.sem.iterdir()))):
            print(f)
            args.sem = f
            try:
                prove(args)
            except KeyboardInterrupt:
                sys.exit(1)
            except:
                errors += 1
                print(f"Error! n={errors}")
                continue
    else:
        created_axioms = prove(args)
        return created_axioms


def prove(args):
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(str(args.sem), parser)
    docs = root.findall('.//document')
    for doc in docs:
        theorem = prove_doc(doc, args.abduction, args)
        premise = clean(theorem.theorems[0].premises[0])
        hypothesis = clean(theorem.theorems[0].conclusion)
        created_axioms = theorem.theorems[0].created_axioms
        if args.write:
            ab_output = str(args.sem).replace('parsed',
                                              'subgoal_matched').replace(
                                                  '.sem.xml', '.txt')
            with codecs.open(ab_output, 'w', 'utf-8') as fout:
                fout.write('Premise:\n')
                fout.write(premise + '\n\n')
                fout.write('Conclusion:\n')
                fout.write(hypothesis + '\n\n')
                fout.write('Subgoals:\n')
                for goal in theorem.theorems[0].subgoals:
                    if goal.split(' ')[0] in theorem.theorems[0].neg_preds:
                        goal += ' : False'
                    fout.write(goal + '\n')
                fout.write('\n')
                fout.write('Axioms:\n')
                for text in created_axioms:
                    fout.write(text + '\n')
    return created_axioms


if __name__ == '__main__':
    main()
