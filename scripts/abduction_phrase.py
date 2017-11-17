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

    def attempt(self, coq_scripts, doc, target, context=None):
        return TryPhraseAbduction(coq_scripts, target)

def TryPhraseAbduction(coq_scripts, target):
    assert len(coq_scripts) == 2
    direct_proof_script = coq_scripts[0]
    reverse_proof_script = coq_scripts[1]
    axioms = set()
    direct_proof_scripts, reverse_proof_scripts = [], []
    inference_result_str, all_scripts = "unknown", []
    while inference_result_str == "unknown":
        #continue abduction for phrase acquisition until inference_result_str matches target
        if target == 'yes':
            #entailment proof
            inference_result_str, direct_proof_scripts, new_direct_axioms = \
                try_phrase_abduction(direct_proof_script,
                              previous_axioms=axioms, expected='yes')
            current_axioms = axioms.union(new_direct_axioms)
        elif target == 'no':
            #contradiction proof
            inference_result_str, reverse_proof_scripts, new_reverse_axioms = \
                try_phrase_abduction(reverse_proof_script,
                              previous_axioms=axioms, expected='no')
            current_axioms = axioms.union(new_reverse_axioms)
        all_scripts = direct_proof_scripts + reverse_proof_scripts
        if len(axioms) == len(current_axioms):
            break
        axioms = current_axioms
    return inference_result_str, all_scripts
    

def try_phrase_abduction(coq_script, previous_axioms=set(), expected='yes'):
    new_coq_script = insert_axioms_in_coq_script(previous_axioms, coq_script)
    current_tactics = get_tactics()
    #debug_tactics = 'repeat nltac_base. try substitution. Qed'
    debug_tactics = 'repeat nltac_base. Qed'
    coq_script_debug = new_coq_script.replace(current_tactics, debug_tactics)
    process = Popen(
        coq_script_debug,
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output_lines = [line.decode('utf-8').strip()
                    for line in process.stdout.readlines()]
    if is_theorem_almost_defined(output_lines):
        return expected, [new_coq_script], previous_axioms
    premise_lines = get_premise_lines(output_lines)
    #for phrase extraction, check all relations between premise_lines and conclusions
    conclusion = get_conclusion_lines(output_lines)
    if not premise_lines or not conclusion:
        failure_log = {"type error": has_type_error(output_lines),
                       "open formula": has_open_formula(output_lines)}
        print(json.dumps(failure_log), file=sys.stderr)
        return 'unknown', [], previous_axioms
    axioms = make_phrase_axioms_from_premises_and_conclusion(premise_lines, conclusion, output_lines, expected)
    #axioms = filter_wrong_axioms(axioms, coq_script) temporarily
    axioms = axioms.union(previous_axioms)
    new_coq_script = insert_axioms_in_coq_script(axioms, coq_script)
    process = Popen(
        new_coq_script,
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output_lines = [line.decode('utf-8').strip()
                    for line in process.stdout.readlines()]
    inference_result_str = expected if is_theorem_almost_defined(output_lines) else 'unknown'
    return inference_result_str, [new_coq_script], axioms

def make_phrase_axioms_from_premises_and_conclusion(premises, conclusions, coq_output_lines=None, expected='yes'):
    axioms = set()
    #check existential variables and if existential variable contain, estimate the probable arguments first
    premises, conclusions = estimate_existential_variables(premises, conclusions)

    for conclusion in conclusions:
        matching_premises = get_premises_that_partially_match_conclusion_args(premises, conclusion)
        premise_preds = [premise.split()[2] for premise in matching_premises]

        #to do: extract all info(cases, variables) about arguments (ex.Subj x1) from get_predicate_arguments-> ask Pascual sensei
        pred_args = get_predicate_arguments(matching_premises, conclusion)
        axioms.update(make_phrase_axioms(premise_preds, conclusion, pred_args, expected))
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
    phrase_axioms = get_phrases(premise_preds, conclusion_pred, pred_args, expected)
    axioms.update(set(phrase_axioms))
    return axioms

def get_phrases(premise_preds, conclusion_pred, pred_args, expected):
    #make phrases based on multiple similarities: surface, external knowledge, argument matching
    #in some cases, considering argument matching only is better
    axiom, axioms = "", []
    src_preds = [denormalize_token(p) for p in premise_preds]
    if "False" in conclusion_pred or "=" in conclusion_pred:
        return list(set(axioms))
    conclusion_pred = conclusion_pred.split()[0]
    trg_pred = denormalize_token(conclusion_pred)
    print("premise_pred:{0}, conclusion_pred:{1}, src_preds:{2}, trg_pred:{3}".format(premise_preds, conclusion_pred, src_preds, trg_pred), file=sys.stderr)

    if len(src_preds) > 1:
        dist = []
        for src_pred in src_preds:
            wordnetsim = calc_wordnetsim(src_pred, trg_pred)
            ngramsim = calc_ngramsim(src_pred, trg_pred)
            argumentsim = calc_argumentsim(src_pred, trg_pred, pred_args)
            #to do: add categorysim or parse score for smoothing argument match error
            #to do: consider how to decide the weight of each info
            # best score: w_1*wordnetsim + w_2*ngramsim + w_3*argumentsim
            # w_1+w_2+w_3 = 1
            # 0 < wordnetsim < 1, 0 < ngramsim < 1, 0 < argumentsim < 1,
            dist.append(distance.cityblock([1, 1, 1], [wordnetsim, ngramsim, argumentsim]))
        maxdist = dist.index(max(dist))

        best_src_pred = src_preds[maxdist]
        best_src_pred_norm = normalize_token(best_src_pred)
        best_src_pred_arg_list = pred_args[best_src_pred_norm]
        best_src_pred_arg = " ".join(best_src_pred_arg_list)

        trg_pred_norm = normalize_token(trg_pred)
        trg_pred_arg_list = pred_args[trg_pred_norm]
        trg_pred_arg = " ".join(trg_pred_arg_list)
        
        total_arg_list = list(set(best_src_pred_arg_list + trg_pred_arg_list))
        total_arg = " ".join(total_arg_list)
        
        axiom = 'Axiom ax_phrase_{0}_{1} : forall {2}, _{0} {3} -> _{1} {4}.'\
                    .format(best_src_pred, trg_pred, total_arg, best_src_pred_arg, trg_pred_arg)

        #print("premise_pred:{0}, conclusion_pred:{1}, pred_args:{2}, axiom:{3}".format(premise_preds, conclusion_pred, pred_args, axiom), file=sys.stderr)
    else:
        axiom = 'Axiom ax_phrase_{0}_{1} : forall {2}, _{0} {3} -> _{1} {4}.'\
                    .format(best_src_pred, trg_pred, total_arg, best_src_pred_arg, trg_pred_arg)
        #print("premise_pred:{0}, conclusion_pred:{1}, pred_args:{2}, axiom:{3}".format(premise_preds, conclusion_pred, pred_args, axiom), file=sys.stderr)

    # to do: consider how to inject antonym axioms
    if expected == "no":
        #make A->B->False axiom
        axiom = re.sub(".", " -> False.", axiom)
    axioms.append(axiom)
    return list(set(axioms))


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

def calc_argumentsim(sub_pred, prem_pred, pred_args):
    sub_pred = normalize_token(sub_pred)
    prem_pred = normalize_token(prem_pred)
    if pred_args[sub_pred] == pred_args[prem_pred]:
        return 1.0
    elif pred_args[sub_pred] in pred_args[prem_pred]:
        #ex. sub_goal: play x0, premise: with x0 x1
        return 0.5
    else:
        return 0.0


def is_theorem_almost_defined(output_lines):
    #check if all content subgoals are deleted(remaining relation subgoals can be permitted)
    #ignore relaional subgoals(False, Acc x0=x1) in the proof
    conclusions = get_conclusion_lines(output_lines)
    #print("conclusion:{0}".format(conclusions), file=sys.stderr)
    if len(conclusions) > 0:
        for conclusion in conclusions:
            if not "False" in conclusion:
                if not "=" in conclusion:
                    return False
    return True

def get_premises_that_partially_match_conclusion_args(premises, conclusion):
    """
    Returns premises where the predicates have at least one argument
    in common with the conclusion.
    """
    candidate_premises = []
    conclusion = re.sub(r'\?([0-9]+)', r'?x\1', conclusion)
    conclusion_args = get_tree_pred_args(conclusion, is_conclusion=True)
    if conclusion_args is None:
        return candidate_premises
    for premise_line in premises:
        # Convert anonymous variables of the form ?345 into ?x345.
        premise_line = re.sub(r'\?([0-9]+)', r'?x\1', premise_line)
        premise_args = get_tree_pred_args(premise_line)
        #print('Conclusion args: ' + str(conclusion_args) +
        #              '\nPremise args: ' + str(premise_args), file=sys.stderr)
        #if tree_contains(premise_args, conclusion_args):
        if premise_args is None or "=" in premise_line:
            # ignore relation premises temporarily
            continue
        else:
            candidate_premises.append(premise_line)
    return candidate_premises

def estimate_existential_variables(premises, conclusions):
    #to do: check existential variables in subgoals and estimate the best variable
    # estimate by number of arguments, case, lexical knowledge??
    # substitute estimated variables for existential variables
    # print("premises:{0}, conclusions:{1}".format(premises, conclusions), file=sys.stderr)
    return list()
