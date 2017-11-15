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
from normalization import denormalize_token, normalize_token
from nltk.corpus import wordnet as wn
import difflib
from scipy.spatial import distance
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
        #entailment proof
        inference_result_str, direct_proof_scripts, new_direct_axioms = \
            try_phrase_abduction(direct_proof_script,
                          previous_axioms=axioms, expected='yes')
        current_axioms = axioms.union(new_direct_axioms)
        reverse_proof_scripts = []
        #contradiction proof
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
    if is_theorem_almost_defined(l.split() for l in output_lines):
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
    axioms = make_phrase_axioms_from_premises_and_conclusion(premise_lines, conclusion, output_lines, expected)
    axioms = filter_wrong_axioms(axioms, coq_script)
    axioms = axioms.union(previous_axioms)
    new_coq_script = insert_axioms_in_coq_script(axioms, coq_script)
    process = Popen(
        new_coq_script,
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output_lines = [line.decode('utf-8').strip().split()
                    for line in process.stdout.readlines()]
    #
    inference_result_str = expected if is_theorem_almost_defined(
        output_lines) else 'unknown'
    return inference_result_str, [new_coq_script], axioms

def make_phrase_axioms_from_premises_and_conclusion(premises, conclusions, coq_output_lines=None, expected='yes'):
    axioms = set()
    for conclusion in conclusions:
        matching_premises = get_premises_that_match_conclusion_args(premises, conclusion)
        premise_preds = [premise.split()[2] for premise in matching_premises]
        conclusion_pred = conclusion.split()[0]
        pred_args = get_predicate_arguments(premises, conclusion)
        axioms.update(make_phrase_axioms(premise_preds, conclusion_pred, pred_args, expected))
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

def make_phrase_axioms(premise_preds, conclusion_pred, pred_args, expected):
    axioms = set()
    if expected == 'yes':
        phrase_axioms = get_phrases(premise_preds, conclusion_pred, pred_args)
        axioms.update(set(phrase_axioms))
        if not axioms:
            approx_axioms = get_probability_phrases(premise_preds, conclusion_pred, pred_args)
            axioms.update(approx_axioms)
    elif expected == 'no':
        #to do: consider how to inject phrase axioms for the proof of contradiction
        phrase_axioms = []
        axioms.update(set(phrase_axioms))

    return axioms

def get_phrases(premise_preds, conclusion_pred, pred_args):
    #make phrases based on argument matching only
    axioms = []
    src_preds = [denormalize_token(p) for p in premise_preds]
    trg_pred = denormalize_token(conclusion_pred)
    #if len(src_preds) > 1:
    #    to do?: select best src_pred
    axiom = 'Axiom ax_phrase_{0}_{1} : forall x, _{0} x -> _{1} x.'\
                .format(src_preds[0], trg_pred)
    print("premise_pred:{0}, conclusion_pred:{1}, pred_args:{2}, axiom:{3}".format(premise_preds, conclusion_pred, pred_args, axiom), file=sys.stderr)
    axioms.append(axiom)
    return list(set(axioms))


def get_probability_phrases(premise_preds, conclusion_pred, pred_args):
    #check existential variables in subgoals and estimate the best argument
    #make phrases based on multiple similarities:surface, external knowledge, category
    axioms = []
    src_preds = [denormalize_token(p) for p in premise_preds]
    trg_pred = denormalize_token(conclusion_pred)
    if len(src_preds) > 1:
        dist = []
        for src_pred in src_preds:
            wordnetsim = calc_wordnetsim(src_pred, trg_pred)
            ngramsim = calc_ngramsim(src_pred, trg_pred)
            #categorysim = calc_categorysim(src_pred, trg_pred)
            dist.append(distance.cityblock([1, 1], [wordnetsim, ngramsim]))
        maxdist = dist.index(max(dist))
        axiom = 'Axiom ax_approx_phrase_{0}_{1} : forall x, _{0} x -> _{1} x.'\
                    .format(src_preds[maxdist], trg_pred)
        axioms.append(axiom)
    else:
        axiom = 'Axiom ax_approx_phrase_{0}_{1} : forall x, _{0} x -> _{1} x.'\
                    .format(src_preds[0], trg_pred)
        axioms.append(axiom)
    return list(set(axioms))

#to do:
#if "no" contains premise sentences, substitute "no" for "a" in the first proof step

#for neutral(STS)
#if the similarity score is in the range of the score(entailment/contradiction, [3-5]),
#create phrase candidates until entailment/contradiction can be proved.

def calc_wordnetsim(sub_pred, prem_pred):
    word_similarity_list = []
    wordFromList1 = wn.synsets(sub_pred)
    wordFromList2 = wn.synsets(prem_pred)
    for w1 in wordFromList1:
        for w2 in wordFromList2:
            if w1.path_similarity(w2) is not None: 
                word_similarity_list.append(w1.path_similarity(w2))
    if(word_similarity_list):
        wordnetsim = max(word_similarity_list)
    else:
        #to do: cannot path similarity but somehow similar
        wordnetsim = 0.5
    return wordnetsim

def calc_ngramsim(sub_pred, prem_pred):
    ngramsim = difflib.SequenceMatcher(None, sub_pred, prem_pred).ratio()
    return ngramsim

def calc_categorysim(sub_pred, prem_pred):
    #to do:extract from sem.xml file
    return categorysim

def is_theorem_almost_defined(output_lines):
    #to do:check if all content subgoals are deleted(remaining relation subgoals is permitted)
    #ignore relaional subgoals(False, Acc x0=x1) in the proof
    for output_line in output_lines:
        if len(output_line) > 2 and 'is defined' in (' '.join(output_line[-2:])):
            return True
    return False
