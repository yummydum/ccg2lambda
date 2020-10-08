# -*- coding: utf-8 -*-
#
#  Copyright 2017 Pascual Martinez-Gomez
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
import logging
import re

from nltk import Tree

from normalization import denormalize_token
from tree_tools import tree_or_string, tree_contains

from graph import Graph, Event, Entity


def find_final_subgoal_line_index(coq_output_lines):
    indices = [
        i for i, line in enumerate(coq_output_lines)
        if line.endswith('subgoal')
    ]
    if not indices:
        return None
    return indices[-1]


def find_final_conclusion_sep_line_index(coq_output_lines):
    indices = [
        i for i, line in enumerate(coq_output_lines)
        if line.startswith('===') and line.endswith('===')
    ]
    if not indices:
        return None
    return indices[-1]


def get_premise_lines(coq_output_lines):
    premise_lines = []
    line_index_last_conclusion_sep = find_final_conclusion_sep_line_index(
        coq_output_lines)
    if not line_index_last_conclusion_sep:
        return premise_lines
    for line in coq_output_lines[line_index_last_conclusion_sep - 1:0:-1]:
        if line == "":
            return premise_lines
        else:
            premise_lines.append(line)
    return premise_lines


def get_conclusion_line(coq_output_lines):
    line_index_last_conclusion_sep = find_final_conclusion_sep_line_index(
        coq_output_lines)
    if not line_index_last_conclusion_sep:
        return None
    return coq_output_lines[line_index_last_conclusion_sep + 1]


def get_premises_that_match_conclusion_args_(premises, conclusion):
    """
    Returns premises where the predicates have at least one argument
    in common with the conclusion.
    This function was used for EACL 2017.
    """
    conclusion_terms = [c.strip(')(') for c in conclusion.split()]
    conclusion_args = set(conclusion_terms[1:])
    candidate_premises = []
    for premise in premises:
        premise_terms = [p.strip(')(') for p in premise.split()[2:]]
        premise_args = set(premise_terms[1:])
        logging.debug('Conclusion args: ' + str(conclusion_args) +
                      '\nPremise args: ' + str(premise_args))
        if premise_args.intersection(conclusion_args):
            candidate_premises.append(premise)
    return candidate_premises


def get_premises_that_match_conclusion_args(premises, conclusion):
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
        logging.debug('Conclusion args: ' + str(conclusion_args) +
                      '\nPremise args: ' + str(premise_args))
        if tree_contains(premise_args, conclusion_args):
            candidate_premises.append(premise_line)
    return candidate_premises


def analyze_coq_output(output_lines):
    """
    Returns a failure log with information about the unproved subgoals.
    """
    failure_log = OrderedDict()
    premise_lines = get_premise_lines(output_lines)
    conclusion = get_conclusion_line(output_lines)
    if not premise_lines or not conclusion:
        failure_log = {
            "type error": has_type_error(output_lines),
            "open formula": has_open_formula(output_lines)
        }
        return failure_log

    matching_premises = get_premises_that_match_conclusion_args(
        premise_lines, conclusion)
    premise_preds = [premise.split()[2] for premise in matching_premises]
    conclusion_pred = conclusion.split()[0]

    failure_log = make_failure_log(conclusion_pred, premise_preds, conclusion,
                                   premise_lines, output_lines)
    return failure_log


def make_failure_log(conclusion_pred,
                     premise_preds,
                     conclusion,
                     premises,
                     coq_output_lines=None):
    """
    Produces a dictionary with the following structure:
    {"unproved sub-goal" : "sub-goal_predicate",
     "matching premises" : ["premise1", "premise2", ...],
     "raw sub-goal" : "conclusion",
     "raw premises" : ["raw premise1", "raw premise2", ...]}
    Raw sub-goal and raw premises are the coq lines with the premise
    internal name and its predicates. E.g.
    H : premise (Acc x1)
    Note that this function is not capable of returning all unproved
    sub-goals in coq's stack. We only return the top unproved sub-goal.
    """
    failure_log = OrderedDict()
    conclusion_base = denormalize_token(conclusion_pred)
    # failure_log["unproved sub-goal"] = conclusion_base
    premises_base = [denormalize_token(p) for p in premise_preds]
    # failure_log["matching premises"] = premises_base
    # failure_log["raw sub-goal"] = conclusion
    # failure_log["raw premises"] = premises
    premise_preds = []
    for p in premises:
        try:
            pred = p.split()[2]
        except:
            continue
        if pred.startswith('_'):
            premise_preds.append(denormalize_token(pred))
    failure_log["all_premises"] = premise_preds
    failure_log["other_sub-goals"] = get_subgoals_from_coq_output(
        coq_output_lines, premises)
    failure_log["other_sub-goals"].insert(
        0, {
            'subgoal': conclusion_base,
            'index': 1,
            'raw_subgoal': conclusion,
            'matching_premises': premises_base,
            'matching_raw_premises': premises_base
        })
    failure_log["type_error"] = has_type_error(coq_output_lines)
    failure_log["open_formula"] = has_open_formula(coq_output_lines)
    return failure_log


def has_type_error(coq_output_lines):
    for line in coq_output_lines:
        if 'has type' in line and 'while it is expected to have type' in line:
            return 'yes'
    return 'no'


def has_open_formula(coq_output_lines):
    for line in coq_output_lines:
        if 'The type of this term is a product while it is expected to be' in line:
            return 'yes'
        if '(fun F' in line:
            return 'yes'
    return 'no'


def get_subgoals_from_coq_output(coq_output_lines, premises):
    """
    When the proving is halted due to unprovable sub-goals,
    Coq produces an output similar to this:

    2 subgoals

      H1 : True
      H4 : True
      x1 : Event
      H6 : True
      H3 : _play x1
      H : _two (Subj x1)
      H2 : _man (Subj x1)
      H0 : _table (Acc x1)
      H5 : _tennis (Acc x1)
      ============================
       _ping (Acc x1)

    subgoal 2 is:
      _pong (Acc x1)

    This function returns the remaining sub-goals ("_pong" in this example).
    """
    subgoals = []
    subgoal_index = -1
    for line in coq_output_lines:
        if line.strip() == '':
            continue
        line_tokens = line.split()
        if subgoal_index > 0:
            subgoal_line = line
            subgoal_tokens = subgoal_line.split()
            subgoal_pred = subgoal_tokens[0]
            if subgoal_index in [s['index'] for s in subgoals]:
                # This sub-goal has already appeared and is recorded.
                subgoal_index = -1
                continue
            subgoal = {
                'subgoal': denormalize_token(line_tokens[0]),
                'index': subgoal_index,
                'raw_subgoal': subgoal_line
            }
            matching_premises = get_premises_that_match_conclusion_args(
                premises, subgoal_line)
            subgoal['matching_raw_premises'] = matching_premises
            premise_preds = [
                denormalize_token(premise.split()[2])
                for premise in matching_premises
            ]
            subgoal['matching_premises'] = premise_preds
            subgoals.append(subgoal)
            subgoal_index = -1
        if len(line_tokens) >= 3 and line_tokens[
                0] == 'subgoal' and line_tokens[2] == 'is:':
            subgoal_index = int(line_tokens[1])
    return subgoals


def parse_coq_line(coq_line):
    try:
        tree_args = tree_or_string('(' + coq_line + ')')
    except ValueError:
        tree_args = None
    return tree_args


def get_tree_pred_args(line, is_conclusion=False):
    """
    Given the string representation of a premise, where each premise is:
      pX : predicate1 (arg1 arg2 arg3)
      pY : predicate2 arg1
    or the conclusion, which is of the form:
      predicate3 (arg2 arg4)
    returns a tree or a string with the arguments of the predicate.
    """
    tree_args = None
    if not is_conclusion:
        tree_args = parse_coq_line(' '.join(line.split()[2:]))
    else:
        tree_args = parse_coq_line(line)
    if tree_args is None or len(tree_args) < 1:
        return None
    return tree_args[0]


def get_tree_pred_args2(line, is_conclusion=False):
    """
    Given the string representation of a premise, where each premise is:
      pX : predicate1 (arg1 arg2 arg3)
      pY : predicate2 arg1
    or the conclusion, which is of the form:
      predicate3 (arg2 arg4)
    returns a tree or a string with the arguments of the predicate.
    """
    tree_args = None
    if not is_conclusion:
        tree_args = parse_coq_line(' '.join(line.split()[2:]))
    else:
        tree_args = parse_coq_line(line)
    if tree_args is None or len(tree_args) < 1:
        return None
    if tree_args.height() >= 3:
        return tree_args[0]  # return subtree
    else:
        return tree_args.leaves()  # return leave args (list, str)


def get_predicate_arguments(premises, conclusion):
    """
    Given the string representations of the premises, where each premises is:
      pX : predicate1 arg1 arg2 arg3
    and the conclusion, which is of the form:
      predicate3 arg2 arg4
    returns a dictionary where the key is a predicate, and the value
    is a list of argument names.
    If the same predicate is found with different arguments, then it is
    labeled as a conflicting predicate and removed from the output.
    Conflicting predicates are typically higher-order predicates, such
    as "Prog".
    """
    pred_args = {}
    pred_trees = []
    for premise in premises:
        try:
            pred_trees.append(
                Tree.fromstring('(' + ' '.join(premise.split()[2:]) + ')'))
        except ValueError:
            continue
    try:
        conclusion_tree = Tree.fromstring('(' + conclusion + ')')
    except ValueError:
        return pred_args
    pred_trees.append(conclusion_tree)

    pred_args_list = []
    for t in pred_trees:
        pred = t.label()
        args = t.leaves()
        pred_args_list.append([pred] + args)
    conflicting_predicates = set()
    for pa in pred_args_list:
        pred = pa[0]
        args = pa[1:]
        if pred in pred_args and pred_args[pred] != args:
            conflicting_predicates.add(pred)
        pred_args[pred] = args
    logging.debug('Conflicting predicates: ' + str(conflicting_predicates))
    for conf_pred in conflicting_predicates:
        del pred_args[conf_pred]
    return pred_args


def make_graph(theorem, premises):
    graph = Graph()
    for premise in premises:
        if '=' in premise:
            premise = premise.replace('=', '')
            name, event, entity = premise.split()
            graph.addRelation(event, entity, name)
        else:
            pred_name = premise.split(' ')[0].split('_')[1]
            arg = premise.split(' ')[1:]
            if len(arg) == 1:
                pos = theorem.pos[pred_name]
                graph.addPred(pred_name, pos, arg)
            elif len(arg) == 2:
                graph.addPreposition(pred_name, arg)
    return graph


def get_matched_premises(theorem):
    output_lines = theorem.output_lines
    premise_lines = get_premise_lines(output_lines)
    conclusion = get_conclusion_line(output_lines)
    subgoals = get_subgoals_from_coq_output2(output_lines)
    premises, subgoals = preprocess(premise_lines, conclusion, subgoals)
    if not premise_lines:
        raise ValueError('Type error')
    elif not subgoals:  # proved?
        return {}
    return create_axioms(theorem, premises, subgoals)


def get_subgoals_from_coq_output2(coq_output_lines):
    subgoals = []
    is_subgoal = False
    for line in coq_output_lines:
        if line.strip() == '':
            continue
        line_tokens = line.split()
        if len(line_tokens) >= 3 and line_tokens[
                0] == 'subgoal' and line_tokens[2] == 'is:':
            is_subgoal = True
        elif is_subgoal:
            subgoals.append(line)
            is_subgoal = False

    return subgoals


def is_sr(e):
    return isinstance(
        e, str) and e.split(' ')[0].lower() in {'subj', 'acc', 'dat'}


def format_subgoal(theorem, subgoal):
    subgoal = subgoal.lstrip('_')
    text, e = subgoal.split(' ')
    if '_' in text:
        if len(text.split('_')) == 3:
            text = '_'.join(text.split('_')[:-1])
        prop, text = text.split('_')
        pos = theorem.pos2[text]
        return f'{prop} {transform(text,pos)}'
    else:
        pos = theorem.pos2[text]
        return transform(text, pos)


def transform(pred, pos):
    if pos.startswith('V'):
        return progressive(pred)
    elif pos.startswith('JJ'):
        return pred
    elif pos.startswith('NN'):
        return f'a {pred}'
    elif pos.startswith('RB'):
        return pred
    else:
        return pred


def progressive(name):
    # TODO change this to spacy or nltk or something
    if name.endswith('ing'):
        return name
    if name.endswith('t'):
        name = name + 't'
    elif name.endswith('e'):
        name = name.rstrip('e')
    return name + 'ing'


def create_axioms(theorem, premises, subgoals):
    result = []
    graph = make_graph(theorem, premises)

    for subgoal in subgoals:
        if is_sr(subgoal):
            assert '=' in subgoal
            x, y = subgoal.split(' = ')
            axiom = f'{graph.get_e(x).get_pred_str()} = {graph.get_e(y).get_pred_str()}'
            breakpoint()
        else:
            arg = get_tree_pred_args2(subgoal, is_conclusion=True)
            if len(arg) == 1:
                e = graph.get_e(arg[0])
                subgoal_text = format_subgoal(theorem, subgoal)
            else:
                # two args means this is a preposition

                subgoal_text = subgoal.split(' ')[0]
                assert arg[0].startswith('e') and arg[1].startswith('x')

                # Event
                e = graph.get_e(arg[0])
                subgoal = f'{e.get_pred_str(subj=False)} & {subgoal}'
                event_str = e.get_pred_str(subj=False, with_ent=False)
                splitted = event_str.split(' ')
                event_str = transform(splitted[0], 'V')
                if len(splitted) > 1:
                    event_str = f"{event_str} {' '.join(splitted[1:])}"
                subgoal_text = f'{event_str} {subgoal_text}'

                # Entity
                e = graph.get_e(arg[1])
                subgoal = f'{e.get_pred_str()} & {subgoal}'
                splitted = e.get_pred_str(with_ent=False).split(' ')
                ent_str = transform(splitted[-1], 'NN')
                if len(splitted) > 1:
                    ent_str = f"{' '.join(splitted[:-1])} {ent_str}"
                subgoal_text = f'{subgoal_text} {ent_str}'

            axiom = f'{e.get_pred_str()} -> {subgoal}'

        axiom_str = f'The {e.get_pred_str(with_ent=False)} is {subgoal_text}'
        result.append([axiom, axiom_str])
    return result


def preprocess(premises, conclusion, subgoals_original):

    if 'False' not in conclusion:
        subgoals_original.append(conclusion)

    # Ununified preds
    subgoals = []
    temp = {}
    for s in sorted(subgoals_original, key=lambda x: len(x.split(' '))):
        s = s.replace('?z', '?x')
        if '?x' in s:
            pred = s.split(' ')[0]
            args = s.split(' ')[1:]
            if len(args) == 1:
                if args[0] not in temp:
                    temp[args[0]] = []
                temp[args[0]].append(pred)
                continue
            elif len(args) == 2:
                for a in args:
                    if '?x' not in a:
                        new_arg = a
                    else:
                        unun_arg = a
                s = f'{pred}{"_".join(temp[unun_arg])} {new_arg}'
                breakpoint()
        subgoals.append(s)

    # Event
    type_prop = [x for x in premises if x.endswith('Event')]
    for t in type_prop:
        var = t.split(' : ')[0]
        e = f'e{var[1:]}'
        # Replace x to e
        for i in range(len(premises)):
            premises[i] = premises[i].replace(var, e)
        for i in range(len(subgoals)):
            subgoals[i] = subgoals[i].replace(var, e)

    # Filter True and Event
    premises = [
        x for x in premises if x.startswith('H') and not x.endswith('True')
    ]

    # semantic role
    premises = sorted(premises, key=lambda x: len(x.split('(')))
    events = set()
    max_ind = 100  # fix this
    result = []
    replace_dict = {}
    for p in premises:
        arg = get_tree_pred_args2(p)
        if isinstance(arg, Tree):
            label = arg.label()
            leave = arg.leaves()
            assert len(leave) == 1
            event = leave[0]
            assert event in events
            original = f'({label} {event})'
            if original in replace_dict:
                ent = replace_dict[original]
            else:
                ent = f'x{max_ind}'
                replace_dict[original] = ent
                max_ind += 1

            result.append(p.replace(original, ent))
            result.append(f'{label} {event} = {ent}')
            for i in range(len(subgoals)):
                subgoals[i] = subgoals[i].replace(original, ent)

        elif isinstance(arg, list):
            for x in arg:
                if x.startswith('e'):
                    events.add(x)
            result.append(p)
        else:
            ValueError()

    # Filter H
    result = [x.split(' : ')[1] if x.startswith('H') else x for x in result]

    # one argument predicate comes in front
    result = sorted(result, key=lambda x: len(x.split(' ')))

    # merge conclucion and subgoals
    return result, subgoals
