#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  Copyright 2017 Hitomi Yanaka
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
from __future__ import print_function
from collections import OrderedDict
import json
import logging
import re
from subprocess import Popen
import subprocess
import sys

from abduction_tools import *
from knowledge import get_tokens_from_xml_node, get_lexical_relations_from_preds
from semantic_tools import is_theorem_defined
from tactics import get_tactics

class AxiomsPhrase(object):
    """
    Create phrasal axioms 
    """
    def __init__(self):
        pass

    def attempt(self, coq_scripts, context=None):
        return TryPhraseAbduction(coq_scripts)

def TryPhraseAbduction(coq_scripts):
    assert len(coq_scripts) == 2
    direct_proof_script = coq_scripts[0]
    reverse_proof_script = coq_scripts[1]
    axioms = set()
    while True:
        inference_result_str, direct_proof_scripts, new_direct_axioms = \
            try_phrase_abduction(direct_proof_script,
                          previous_axioms=axioms, expected='yes')
        current_axioms = axioms.union(new_direct_axioms)
        reverse_proof_scripts = []
        if not inference_result_str == 'yes':
            inference_result_str, reverse_proof_scripts, new_reverse_axioms = \
                try_phrase_abduction(reverse_proof_script,
                              previous_axioms=current_axioms, expected='no')
            current_axioms.update(new_reverse_axioms)
        all_scripts = direct_proof_scripts + reverse_proof_scripts
        if len(axioms) == len(current_axioms) or inference_result_str != 'unknown':
            break
        axioms = current_axioms
    return inference_result_str, all_scripts
    

def try_phrase_abduction(coq_script, previous_axioms=set(), expected='yes'):
    new_coq_script = insert_axioms_in_coq_script(previous_axioms, coq_script)
    current_tactics = get_tactics()
    debug_tactics = 'repeat nltac_base. try substitution. Qed'
    coq_script_debug = new_coq_script.replace(current_tactics, debug_tactics)
    process = Popen(
        coq_script_debug,
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output_lines = [line.decode('utf-8').strip()
                    for line in process.stdout.readlines()]
    if is_theorem_defined(l.split() for l in output_lines):
        return expected, [new_coq_script], previous_axioms
    premise_lines = get_premise_lines(output_lines)
    #for phrase extraction, check all relations between premise_lines and conclusions
    conclusion = get_conclusion_lines(output_lines)
    #print("premise:{0}, conclusion:{1}".format(premise_lines, conclusion), file=sys.stderr)
    if not premise_lines or not conclusion:
        failure_log = {"type error": has_type_error(output_lines),
                       "open formula": has_open_formula(output_lines)}
        print(json.dumps(failure_log), file=sys.stderr)
        return 'unknown', [], previous_axioms
    axioms = make_phrase_axioms_from_premises_and_conclusion(
        premise_lines, conclusion, output_lines)
    axioms = filter_wrong_axioms(axioms, coq_script)
    axioms = axioms.union(previous_axioms)
    new_coq_script = insert_axioms_in_coq_script(axioms, coq_script)
    process = Popen(
        new_coq_script,
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output_lines = [line.decode('utf-8').strip().split()
                    for line in process.stdout.readlines()]
    inference_result_str = expected if is_theorem_defined(
        output_lines) else 'unknown'
    return inference_result_str, [new_coq_script], axioms

def make_phrase_axioms_from_premises_and_conclusion(premises, conclusions, coq_output_lines=None):
    axioms = set()
    for conclusion in conclusions:
        matching_premises = get_premises_that_match_conclusion_args(premises, conclusion)
        premise_preds = [premise.split()[2] for premise in matching_premises]
        conclusion_pred = conclusion.split()[0]
        pred_args = get_predicate_arguments(premises, conclusion)
    axioms.update(make_phrase_axioms(premise_preds, conclusion_pred, pred_args))
        #if not axioms:
        #    failure_log = make_failure_log(
        #        conclusion_pred, premise_preds, conclusion, premises, coq_output_lines)
        #    print(json.dumps(failure_log), file=sys.stderr)
    return axioms

def get_conclusion_lines(coq_output_lines):
    conclusion_lines = []
    line_index_last_conclusion_sep = find_final_conclusion_sep_line_index(coq_output_lines)
    if not line_index_last_conclusion_sep:
        return None
    for line in coq_output_lines[line_index_last_conclusion_sep+1:]:
        if re.search('Toplevel', line):
            return conclusion_lines
        elif line == '':
            continue
        elif re.search('subgoal', line):
            continue
        elif re.search('repeat nltac_base', line):
            return conclusion_lines
        else:
            conclusion_lines.append(line)
    return conclusion_lines

def make_phrase_axioms(premise_preds, conclusion_pred, pred_args):
    axioms = set()
    print("premise_pred:{0}, conclusion_pred:{1}, pred_args:{2}".format(premise_preds, conclusion_pred, pred_args), file=sys.stderr)
    #phrase_axioms = get_phrase_candidates(premise_preds, conclusion_pred, pred_args)
    #axioms.update(set(phrase_axioms))
    # if not axioms:
    #   approx_axioms = GetApproxRelationsFromPreds(premise_preds, conclusion_pred)
    #   axioms.update(approx_axioms)
    return axioms