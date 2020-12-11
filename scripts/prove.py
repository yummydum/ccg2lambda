#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#  Copyright 2015 Pascual Martinez-Gomez
#  Copyright 2020 Riko Suzuki
#  Copyright 2021 Atsushi Sumita
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

import json
import sys
import argparse
import codecs
import logging
from lxml import etree
import sys
from subprocess import TimeoutExpired
from pathlib import Path
from tqdm import tqdm
from semantic_tools import prove_doc
from theorem import clean

logging.basicConfig(level=logging.WARNING)


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
        # Loop over the pairs
        errors = dict()
        files = sorted([f for f in args.sem.iterdir()])
        for f in tqdm(files):
            print(f)
            args.sem = f
            theorem = prove(args)
            if theorem is None:
                pass
            elif theorem.error_message is not None:
                e = str(theorem.error_message)
                if e not in errors:
                    errors[e] = 0
                errors[e] += 1
                print(e)

    else:
        return prove(args)


def prove(args):
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(str(args.sem), parser)
    docs = root.findall('.//document')
    assert len(docs) == 1
    doc = docs[0]
    args.id = int(args.sem.name.replace('.sem.xml', '').replace('pair_', ''))

    try:
        theorem = prove_doc(doc, args.abduction, args).theorems[0]
    # TODO: see why timeout happens
    except TimeoutExpired:
        return
    # parse error?
    except AttributeError:
        return

    result = {}
    result["pair_id"] = args.id
    result["premise"] = theorem.original
    result["conclusion"] = theorem.original2
    result["premise_formula"] = clean(theorem.premises[0])
    result["conclusion_formula"] = clean(theorem.conclusion)
    result["subgoals"] = theorem.subgoal
    result["created_axioms"] = theorem.created_axioms
    result["readable_subgoals"] = theorem.readable_subgoals
    result["prediction"] = theorem.result2
    fn = args.sem.name.replace("xml", "json")
    if args.abduction is None:
        ab_output = f"data/created_axioms/{fn}"
    else:
        ab_output = f"data/created_axioms_abduction/{fn}"
    with codecs.open(ab_output, 'w', 'utf-8') as f:
        json.dump(result, f)

    return theorem


if __name__ == '__main__':
    main()
