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

import argparse
import codecs
import logging
from lxml import etree
from multiprocessing import Pool
from multiprocessing import Lock
import os
from subprocess import TimeoutExpired
import sys
import textwrap

from semantic_tools import prove_doc
from semparse import serialize_tree
from utils import time_count
from visualization_tools import convert_root_to_mathml
from theorem import clean

ARGS = None
DOCS = None
ABDUCTION = None
kMaxTasksPerChild = None
lock = Lock()
MATCHED_PREMISES = {}
PREMISE = ''
HYPOTHESIS = ''


def main():
    global ARGS
    global DOCS
    global ABDUCTION
    global MATCHED_PREMISES
    global PREMISE
    global HYPOTHESIS

    DESCRIPTION = textwrap.dedent("""\
            The input file sem should contain the parsed sentences. All CCG trees correspond
            to the premises, except the last one, which is the hypothesis.
      """)

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=DESCRIPTION)
    parser.add_argument("sem", help="XML input filename with semantics")
    parser.add_argument("--proof",
                        default="",
                        help="XML output filename with proof information")
    parser.add_argument("--graph_out",
                        nargs='?',
                        type=str,
                        default="",
                        help="HTML graphical output filename.")
    parser.add_argument(
        "--abduction",
        nargs='?',
        type=str,
        default="no",
        choices=["no", "naive", "spsa"],
        help="Activate on-demand axiom injection (default: no axiom injection)."
    )
    parser.add_argument("--gold_trees", action="store_true", default=True)
    parser.add_argument(
        "--print",
        nargs='?',
        type=str,
        default="result",
        choices=["result", "status", "both"],
        help=
        "Print to standard output the inference result or termination status.")
    parser.add_argument("--print_length",
                        nargs='?',
                        type=str,
                        default="full",
                        choices=["full", "short", "zero"],
                        help="Length of printed output.")
    parser.add_argument("--timeout",
                        nargs='?',
                        type=int,
                        default="100",
                        help="Maximum running time for each possible theorem.")
    parser.add_argument("--ncores",
                        nargs='?',
                        type=int,
                        default="1",
                        help="Number of cores for multiprocessing.")
    parser.add_argument("--subgoals", action="store_true", default=False)
    parser.add_argument("--subgoals_out",
                        nargs='?',
                        type=str,
                        default="",
                        help="subgoals output filename.")
    parser.add_argument("--bidirection", action="store_true", default=False)
    ARGS = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)

    if not os.path.exists(ARGS.sem):
        print('File does not exist: {0}'.format(ARGS.sem), file=sys.stderr)
        parser.print_help(file=sys.stderr)
        sys.exit(1)

    if ARGS.abduction == "spsa":
        from abduction_spsa import AxiomsWordnet
        ABDUCTION = AxiomsWordnet()
    elif ARGS.abduction == "naive":
        from abduction_naive import AxiomsWordnet
        ABDUCTION = AxiomsWordnet()

    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(ARGS.sem, parser)

    DOCS = root.findall('.//document')
    document_inds = range(len(DOCS))
    proof_nodes = prove_docs(document_inds, ARGS.ncores)
    assert len(proof_nodes) == len(DOCS), \
        'Num. elements mismatch: {0} vs {1}'.format(len(proof_nodes), len(DOCS))
    for doc, proof_node in zip(DOCS, proof_nodes):
        doc.append(proof_node)

    if ARGS.proof:
        serialize_tree_to_file(root, ARGS.proof)

    if ARGS.graph_out:
        html_str = convert_root_to_mathml(root, ARGS.gold_trees)
        with codecs.open(ARGS.graph_out, 'w', 'utf-8') as fout:
            fout.write(html_str)

    if ARGS.subgoals_out:
        AB_output = ARGS.subgoals_out
        with codecs.open(AB_output, 'w', 'utf-8') as fout:
            fout.write('Premise:\n')
            fout.write(PREMISE + '\n\n')
            fout.write('Conclusion:\n')
            fout.write(HYPOTHESIS + '\n\n')
            for unproved, matched in MATCHED_PREMISES.items():
                fout.write('Unproved: ' + unproved + '\n')
                fout.write('Matched premises: ')
                for e, p in matched['premise'].items():
                    fout.write(f'E: {e}, ' + ','.join(p) + '\n\n')


@time_count
def serialize_tree_to_file(tree_xml, fname):
    root_xml_str = serialize_tree(tree_xml)
    with codecs.open(fname, 'wb') as fout:
        fout.write(root_xml_str)
    return


@time_count
def prove_docs(document_inds, ncores=1):
    if ncores <= 1:
        proof_nodes = prove_docs_seq(document_inds)
    else:
        proof_nodes = prove_docs_par(document_inds, ncores)
    #print('', file=sys.stdout)
    proof_nodes = [etree.fromstring(p) for p in proof_nodes]
    return proof_nodes


def prove_docs_par(document_inds, ncores=3):
    pool = Pool(processes=ncores, maxtasksperchild=kMaxTasksPerChild)
    proof_nodes = pool.map(prove_doc_ind, document_inds)
    pool.close()
    pool.join()
    return proof_nodes


def prove_docs_seq(document_inds):
    proof_nodes = []
    for document_ind in document_inds:
        proof_node = prove_doc_ind(document_ind)
        proof_nodes.append(proof_node)
    return proof_nodes


def prove_doc_ind(document_ind):
    """
    Perform RTE inference for the document ID document_ind.
    It returns an XML node with proof information.
    """
    global MATCHED_PREMISES
    global PREMISE
    global HYPOTHESIS
    global lock
    doc = DOCS[document_ind]
    proof_node = etree.Element('proof')
    inference_result = 'unknown'
    try:
        theorem = prove_doc(doc, ABDUCTION, ARGS)
        PREMISE = clean(theorem.theorems[0].premises[0])
        HYPOTHESIS = clean(theorem.theorems[0].conclusion)
        MATCHED_PREMISES = theorem.theorems[0].matched_premises
        proof_node.set('status', 'success')
        inference_result = theorem.result
        proof_node.set('inference_result', inference_result)
        inference_result_rev = theorem.result_rev
        if inference_result_rev is not None:
            proof_node.set('inference_result_rev', inference_result_rev)
        theorems_node = theorem.to_xml()
        proof_node.append(theorems_node)
    except TimeoutExpired as e:
        proof_node.set('status', 'timedout')
        proof_node.set('inference_result', 'unknown')
        proof_node.set('inference_result_rev', 'unknown')
    except Exception as e:
        doc_id = doc.get('id', '(unspecified)')
        proof_node.set('status', 'failed')
        proof_node.set('inference_result', 'unknown')
        proof_node.set('inference_result_rev', 'unknown')
        raise ValueError()
    return etree.tostring(proof_node)


if __name__ == '__main__':
    main()
