#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  Copyright 2017 Pascual Martinez-Gomez
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

from collections import OrderedDict
import itertools
import logging
from lxml import etree
import subprocess
import re
import json
from pathlib import Path

from coq_analyzer import analyze_coq_output, get_premise_lines, get_subgoals_from_coq_output2, get_conclusion_line
from nltk2coq import normalize_interpretation
from semantic_types import get_dynamic_library_from_doc
from tactics import get_tactics
from normalization import substitute_invalid_chars
from nltk2normal import rename_variable, convert_to_prenex, remove_true, get_negated_subtree
from nltk.sem.logic import Expression
from graph import Graph


def normalize(x):
    return convert_to_prenex(rename_variable(remove_true(x)))


def clean(x):
    x = str(normalize(x))
    x = x.replace('.(', '.(\n').replace(' & ', ' & \n')
    x = x[:-1] + '\n)'
    return x


class Theorem(object):
    """
    Manage a theorem and its variations.
    """
    def __init__(self,
                 premises,
                 conclusion,
                 axioms=None,
                 dynamic_library_str='',
                 is_negated=False,
                 is_reversed=False):
        premises = [rename_variable(remove_true(x)) for x in premises]
        conclusion = rename_variable(remove_true(conclusion))
        self.premises = premises
        self.conclusion = conclusion
        self.axioms = set() if axioms is None else axioms
        self.dynamic_library_str = dynamic_library_str
        self.inference_result = None
        self.coq_script = None
        self.output_lines = None
        self.matched_premises = None
        self.is_negated = is_negated
        self.is_reversed = is_reversed
        self.can_reverse = True
        self.variations = []
        self.doc = None
        self.failure_log = None
        self.timeout = 100
        self.labels = []
        self.subgoal = []  # very bad naming...
        self.subgoals = []
        self.created_axioms = []
        self.readable_subgoals = []
        self.output_lines = []
        self.result2 = "neutral"
        self.error_message = None
        self.use_readable_subgoal = None

    def __repr__(self):
        return self.coq_script

    def __hash__(self):
        return hash(self.coq_script)

    def __eq__(self, other):
        return isinstance(other,
                          Theorem) and self.coq_script == other.coq_script

    @staticmethod
    def from_doc(doc):
        """
        Build a theorem from an XML document produced by semparse.py script.
        """
        formulas = get_formulas_from_doc(doc)
        if not formulas or len(formulas) < 2:
            return Theorem([], '', set(), '')
        dynamic_library_str, formulas = get_dynamic_library_from_doc(
            doc, formulas)
        premises, conclusion = formulas[:-1], formulas[-1]
        theorem = Theorem(premises, conclusion, set(), dynamic_library_str)
        theorem.doc = doc
        return theorem

    def copy(self,
             new_premises=None,
             new_conclusion=None,
             new_axioms=None,
             is_negated=None,
             is_reversed=None):
        if new_premises is None:
            new_premises = self.premises
        if new_conclusion is None:
            new_conclusion = self.conclusion
        if new_axioms is None:
            new_axioms = self.axioms
        if is_negated is None:
            is_negated = self.is_negated
        if is_reversed is None:
            is_reversed = self.is_reversed
        theorem = Theorem(new_premises,
                          new_conclusion,
                          new_axioms,
                          self.dynamic_library_str,
                          is_negated=is_negated,
                          is_reversed=is_reversed)
        theorem.doc = self.doc
        theorem.timeout = self.timeout
        self.variations.append(theorem)
        return theorem

    def negate(self):
        negated_conclusion = negate_conclusion(self.conclusion)
        theorem = self.copy(new_conclusion=negated_conclusion,
                            is_negated=not self.is_negated)
        return theorem

    def reverse(self, is_negated=None):
        if len(self.premises) != 1:
            self.can_reverse = False
            return None
        if is_negated is None:
            is_negated = self.is_negated
        theorem = self.copy([self.conclusion],
                            self.premises[0],
                            is_reversed=not self.is_reversed,
                            is_negated=is_negated)
        return theorem

    @property
    def all_subgoals(self):
        lst = []
        for theorem in self.variations:
            lst.append(theorem.subgoals)
        return lst

    @property
    def result(self):
        for theorem in self.variations:
            if not theorem.is_reversed:
                if theorem.result_simple != 'unknown':
                    return theorem.result_simple
        return 'unknown'

    @property
    def result_rev(self):
        for theorem in self.variations:
            if not self.can_reverse:
                return None
            else:
                if theorem.is_reversed:
                    if theorem.result_simple != 'unknown':
                        return theorem.result_simple
        return 'unknown'

    @property
    def result_simple(self):
        if self.inference_result is True and self.is_negated is False:
            return 'yes'
        elif self.inference_result is True and self.is_negated is True:
            return 'no'
        else:
            return 'unknown'

    def prove_debug(self, axioms=None, use_noneg=False):
        failure_log = OrderedDict()
        if use_noneg:
            conclusion = self.conclusion_noneg
        else:
            conclusion = self.conclusion
        coq_script = make_coq_script(self.premises,
                                     conclusion,
                                     self.dynamic_library_str,
                                     axioms=axioms)

        current_tactics = get_tactics()
        debug_tactics = 'repeat nltac_base. try substitution. Qed'
        coq_script = coq_script.replace(current_tactics, debug_tactics)
        output_lines = run_coq_script(coq_script, self.timeout)
        self.output_lines = output_lines

        if is_theorem_defined(output_lines):
            self.inference_result = True
            self.coq_script = coq_script
            self.failure_log = failure_log
            return True, failure_log

        failure_log = analyze_coq_output(output_lines)
        return False, failure_log

    def prove_simple(self):
        self.coq_script = make_coq_script(self.premises, self.conclusion,
                                          self.dynamic_library_str,
                                          self.axioms)
        self.inference_result = prove_script(self)
        return

    def prove(self, abduction=None):

        print('simple prove')
        self.prove_simple()
        if self.inference_result:
            self.result2 = 'entailment'
            return

        self.variations.append(self)

        # contradiction (whole scope)
        neg_theorem = self.negate()
        print('P -> not H')
        neg_theorem.prove_simple()
        if neg_theorem.inference_result:
            self.inference_result = True
            self.result2 = 'contradiction'
            return

        if abduction and self.doc is not None:
            print('abduction')
            abduction_theorem = abduction.attempt(self)
            if abduction_theorem.inference_result:
                self.inference_result = True
                self.result2 = 'entailment'
                return

        if self.use_readable_subgoal:
            print("P -> H with readable subgoal")
            created_axioms = self.get_readable_subgoals()
            self.prove_debug(axioms=created_axioms)
            logging.debug(self.coq_script)
            logging.debug("\n".join(self.output_lines))
            if self.inference_result:
                print('proved by readable subgoal')
                self.result2 = "entailment"
                return

            print('P -> not H with readable subgoal')
            neg_theorem.prove_debug(axioms=created_axioms)
            if neg_theorem.inference_result:
                self.inference_result = True
                self.result2 = 'contradiction'
                print('proved by readable subgoal & negation')
                return
        print("not proved")
        return

    def get_readable_subgoals(self):
        p = self.created_subgoal_path()
        with p.open(mode="r") as f:
            data = json.load(f)
        return data["created_axioms"]

    def create_readable_subgoals(self):

        # Make noneg output
        self.prove_debug(use_noneg=True)
        if self.inference_result:
            self.result2 = 'contradiction'
            return

        g = Graph(self)

        output_lines = self.output_lines
        premise_line = get_premise_lines(output_lines)
        g.addPremise(premise_line)

        subgoal_line = get_subgoals_from_coq_output2(output_lines)
        subgoal_line.append(get_conclusion_line(output_lines))
        g.addSubgoals(subgoal_line)

        # graph.visualize()
        readable_subgoals, created_axioms = g.create_readable_subgoals()

        # format results
        result = {}
        result["pair_id"] = self.id
        result["premise"] = " ".join(g.premise)
        result["conclusion"] = " ".join(g.hypothesis)
        result["premise_formula"] = clean(self.premises[0])
        result["conclusion_formula"] = clean(self.conclusion)
        result["subgoals"] = self.subgoal
        result["created_axioms"] = created_axioms
        result["readable_subgoals"] = readable_subgoals
        result["prediction"] = self.result2

        # save
        p = self.created_subgoal_path()
        with p.open(mode="w") as f:
            json.dump(result, f)
        return

    def created_subgoal_path(self):
        fn = self.sem.name.replace("xml", "json")
        return Path(f"data/created_axioms/{fn}")

    def create_noneg_conclusion(self):
        neg_tree = get_negated_subtree(self.conclusion)
        if neg_tree:
            neg_str = str(neg_tree[0])
            pos_str = str(neg_tree[0].negate())
            conclusion = str(self.conclusion).replace(neg_str, pos_str)
            self.conclusion_noneg = Expression.fromstring(conclusion)
        else:
            self.conclusion_noneg = self.conclusion
        return

    def get_subgoals(self, abduction=None):
        for theorem in self.variations:
            if not theorem.is_negated:
                coq_script = make_coq_script(theorem.premises,
                                             theorem.conclusion,
                                             theorem.dynamic_library_str,
                                             axioms=theorem.axioms)
                current_tactics = get_tactics()
                debug_tactics = 'Set Firstorder Depth 1. nltac. Set Firstorder Depth 3. repeat nltac_base. Qed'
                coq_script = coq_script.replace(current_tactics, debug_tactics)
                output_lines = run_coq_script(coq_script, self.timeout)

                theorem.subgoals = get_subgoal_lines(output_lines)
        return

    def to_xml(self):
        ts_node = etree.Element('theorems')
        if self.labels:
            ts_node.append(make_parser_labels_node(self.labels))
        # Add premises node.
        ps_node = etree.Element('premises')
        ts_node.append(ps_node)
        for premise in self.premises:
            p_node = etree.Element('premise')
            p_node.text = str(premise)
            ps_node.append(p_node)
        # Add conclusion node.
        c_node = etree.Element('conclusion')
        c_node.text = str(self.conclusion)
        ts_node.append(c_node)
        # Add dynamic library.
        d_node = etree.Element('dynamic_library')
        d_node.text = self.dynamic_library_str
        ts_node.append(d_node)
        # Add direct and reverse theorem.
        direct_node = etree.Element('direct_definition')
        direct_node.text = make_coq_formulae(self.premises, self.conclusion)
        ts_node.append(direct_node)

        reverse_node = etree.Element('reverse_definition')
        reverse_node.text = make_coq_formulae(self.premises,
                                              self.conclusion,
                                              reverse=True)
        ts_node.append(reverse_node)

        direct_node_neg = etree.Element('direct_definition_neg')
        direct_node_neg.text = make_coq_formulae(
            self.premises, negate_conclusion(self.conclusion))
        ts_node.append(direct_node_neg)

        reverse_node_neg = etree.Element('reverse_definition_neg')
        reverse_node_neg.text = make_coq_formulae(self.premises,
                                                  negate_conclusion(
                                                      self.conclusion),
                                                  reverse=True)
        ts_node.append(reverse_node_neg)
        # Add theorem(s) node.
        for theorem in self.variations:
            t_node = etree.Element('theorem')
            ts_node.append(t_node)
            if theorem.failure_log is None:
                _, failure_log = theorem.prove_debug()
            t_node.set('inference_result', theorem.result_simple)
            t_node.set('is_negated', str(theorem.is_negated))
            t_node.set('is_reversed', str(theorem.is_reversed))
            s_node = etree.Element('coq_script')
            s_node.text = theorem.coq_script
            t_node.append(s_node)
            f_node = make_failure_log_node(failure_log)
            t_node.append(f_node)
            g_node = etree.Element('subgoals')
            g_node.text = ','.join(theorem.subgoals)
            t_node.append(g_node)
        return ts_node


def make_parser_labels_node(labels):
    ls_node = etree.Element('parser_labels')
    for label in labels:
        assert len(label) == 2
        l_node = etree.Element('parser_label')
        l_node.set('ccg_id', str(label[0]))
        l_node.set('ccg_parser', str(label[1]))
        ls_node.append(l_node)
    return ls_node


def make_failure_log_node(failure_log):
    fnode = etree.Element('failure_log')
    if not failure_log:
        return fnode
    if 'all_premises' in failure_log:
        n = etree.Element('all_premises')
        fnode.append(n)
        for p in failure_log.get('all_premises', []):
            pn = etree.Element('premise')
            n.append(pn)
            pn.text = p
    fnode.set('type_error', failure_log.get('type_error', 'unk'))
    fnode.set('open_formula', failure_log.get('open_formula', 'unk'))
    if 'other_sub-goals' in failure_log:
        n = etree.Element('other_sub-goals')
        fnode.append(n)
        for g in failure_log.get('other_sub-goals', []):
            gn = etree.Element('subgoal')
            n.append(gn)
            gn.set('predicate', g['subgoal'])
            gn.set('index', str(g['index']))
            gn.set('line', g['raw_subgoal'])

            pns = etree.Element('matching_premises')
            gn.append(pns)
            for prem in g.get('matching_premises', []):
                pn = etree.Element('matching_premise')
                pns.append(pn)
                pn.set('predicate', prem)

            pns = etree.Element('matching_raw_premises')
            gn.append(pns)
            for prem in g.get('matching_raw_premises', []):
                pn = etree.Element('matching_raw_premise')
                pns.append(pn)
                pn.set('line', prem)
    return fnode


def get_formulas_from_doc(doc):
    """
    Returns string representations of logical formulas,
    as stored in the "sem" attribute of the root node
    of semantic trees.
    If a premise has no semantic representation, it is ignored.
    If there are no semantic representation at all, or the conclusion
    has no semantic representation, it returns None to signal an error.
    """
    # TODO: we need to parameterize the way we obtain formulas for N-best parsing.
    formulas = [
        s.get('sem', None)
        for s in doc.xpath('./sentences/sentence/semantics[1]/span[1]')
    ]
    if len(formulas) < 2 or formulas[-1] == None:
        return None
    formulas = [f for f in formulas if f is not None]
    return formulas


def make_coq_formulae(premise_interpretations, conclusion, reverse=False):
    interpretations = premise_interpretations + [conclusion]
    interpretations = [
        normalize_interpretation(interp) for interp in interpretations
    ]
    if reverse:
        interpretations.reverse()
    coq_formulae = ' -> '.join(interpretations)
    return coq_formulae


def make_coq_script(premise_interpretations,
                    conclusion,
                    dynamic_library='',
                    axioms=None):
    # Transform these interpretations into coq format:
    #   interpretation1 -> interpretation2 -> ... -> conclusion
    coq_formulae = make_coq_formulae(premise_interpretations, conclusion)

    # Input these formulae to coq and retrieve the results.
    tactics = get_tactics()
    coq_script = "Require Export coqlib.\n{0}\nTheorem t1: {1}. {2}.".format(
        dynamic_library, coq_formulae, tactics)
    if axioms is not None and len(axioms) > 0:
        coq_script = insert_axioms_in_coq_script(axioms, coq_script)
    coq_script = substitute_invalid_chars(coq_script, 'replacement.txt')
    return coq_script


def prove_script(self):
    output_lines = run_coq_script(self.coq_script, self.timeout)
    self.output_lines = output_lines
    return is_theorem_defined(output_lines)


def run_coq_script(coq_script, timeout=100):
    """
    Receives coq script of the form:
      Require Export coqlib.
      Parameter ...
      Parameter ...
      Theorem t1 ... <tactics>. Qed.
    Returns the output lines.
    """
    coq_script = substitute_invalid_chars(coq_script, 'replacement.txt')
    try:
        ps = subprocess.Popen(('echo', coq_script), stdout=subprocess.PIPE)
        output = subprocess.check_output(('coqtop', ),
                                         stdin=ps.stdout,
                                         stderr=subprocess.STDOUT,
                                         timeout=timeout)
        ps.wait()
    except subprocess.CalledProcessError as e:
        logging.error(
            'Error when running the following script:\n{0}\nMessage was: {1}'.
            format(coq_script, e))
        return []
    output_lines = [
        str(line).strip() for line in output.decode('utf-8').split('\n')
    ]
    return output_lines


# Given a string reprsenting the logical interpretation of the conclusion,
# it returns a string with the negated conclusion.
def negate_conclusion(conclusion):
    return -conclusion


# Check whether the string "is defined" appears in the output of coq.
# In that case, we return True. Otherwise, we return False.
def is_theorem_defined(output_lines):
    for output_line in output_lines:
        if len(output_line) > 2 and 'No more subgoals.' in output_line:
            return True
        elif len(output_line) > 2 and 'No such goal.' in output_line:
            return True
    return False


def is_theorem_error(output_lines):
    """
    Errors in the construction of a theorem (type mismatches in axioms, etc.)
    are signaled using the symbols ^^^^ indicating where the error is.
    We simply search for that string.
    """
    return any('^^^^' in ol for ol in output_lines)


def get_theorem_line(coq_script_lines):
    for i, line in enumerate(coq_script_lines):
        if line.startswith('Theorem '):
            return i
    assert False, 'There was no theorem defined in the coq script: {0}'\
        .format('\n'.join(coq_script_lines))


def insert_axioms_in_coq_script(axioms, coq_script):
    coq_script_lines = coq_script.split('\n')
    theorem_line = get_theorem_line(coq_script_lines)
    for axiom in axioms:
        axiom_name = axiom.split()[1]
        coq_script_lines.insert(theorem_line,
                                'Hint Resolve {0}.'.format(axiom_name))
        coq_script_lines.insert(theorem_line, axiom)
    new_coq_script = '\n'.join(coq_script_lines)
    return new_coq_script


# TODO: Move this to another file.
class MasterTheorem(Theorem):
    """
    Produce multiple theorems derived from the combination of
    different semantic interpretations of sentences. Check those
    theorems and build an ensemble of judgements.
    """
    def __init__(self, theorems=None):
        self.theorems = [] if theorems is None else theorems
        self.doc = None
        self.inference_result = None
        self.failure_log = None
        self.timeout = 100

    def __repr__(self):
        return '\n'.join(t.coq_script for t in self.theorems)

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        return isinstance(
            other, MasterTheorem) and self.__hash__() == other.__hash__()

    @staticmethod
    def from_doc(doc, args=None):
        """
        Build multiple theorems from an XML document produced by semparse.py script.
        """
        use_gold_trees = False if args is None else args.gold_trees
        timeout = 100 if args is None else args.timeout
        theorems = []
        for semantics in generate_semantics_from_doc(doc, 100, use_gold_trees):
            formulas = [sem.xpath('./span[1]/@sem')[0] for sem in semantics]
            assert formulas and len(formulas) > 1
            dynamic_library_str, formulas = get_dynamic_library_from_doc(
                doc, semantics)
            premises, conclusion = formulas[:-1], formulas[-1]
            theorem = Theorem(premises, conclusion, set(), dynamic_library_str)
            labels = [(s.get('ccg_id', None), s.get('ccg_parser', None))
                      for s in semantics]
            theorem.labels = labels
            theorem.doc = doc
            theorem.use_readable_subgoal = args.use_readable_subgoal
            theorem.id = args.id
            theorem.timeout = timeout
            theorem.sem = args.sem
            theorems.append(theorem)
        master_theorem = MasterTheorem(theorems)
        master_theorem.timeout = timeout
        return master_theorem

    @staticmethod
    def from_doc_rev(doc, args=None):
        """
        Build multiple theorems from an XML document produced by semparse.py script.
        """
        use_gold_trees = False if args is None else args.gold_trees
        timeout = 100 if args is None else args.timeout
        theorems = []
        for semantics in generate_semantics_from_doc(doc, 100, use_gold_trees):
            formulas = [sem.xpath('./span[1]/@sem')[0] for sem in semantics]
            assert formulas and len(formulas) > 1
            dynamic_library_str, formulas = get_dynamic_library_from_doc(
                doc, semantics)
            premises, conclusion = formulas[:-1], formulas[-1]
            theorem = Theorem(premises, conclusion, set(), dynamic_library_str)
            theorem = theorem.reverse()
            labels = [(s.get('ccg_id', None), s.get('ccg_parser', None))
                      for s in semantics]
            theorem.labels = labels
            theorem.doc = doc
            theorem.timeout = timeout
            theorems.append(theorem)
        master_theorem = MasterTheorem(theorems)
        master_theorem.timeout = timeout
        return master_theorem

    def prove(self, abduction=None):
        for theorem in self.theorems:
            theorem.prove(abduction)
            if theorem.result != 'unknown':
                break
        return

    def get_subgoals(self, abduction=None):
        for theorem in self.theorems:
            theorem.get_subgoals(abduction)
        return

    @property
    def all_subgoals(self):
        lst = []
        for theorem in self.theorems:
            lst.append(theorem.all_subgoals)
        return lst

    @property
    def result(self):
        for theorem in self.theorems:
            if theorem.result != 'unknown':
                return theorem.result
        return 'unknown'

    @property
    def result_rev(self):
        for theorem in self.theorems:
            if theorem.result_rev != 'unknown':
                return theorem.result_rev
        return 'unknown'

    def get_best_theorem(self):
        if not self.theorems:
            return None
        for theorem in self.theorems:
            if theorem.result != 'unknown':
                return theorem
        return self.theorems[0]

    def to_xml_(self):
        theorem = self.get_best_theorem()
        if not theorem:
            ts_node = etree.Element('theorems')
        else:
            ts_node = theorem.to_xml()
        return ts_node

    def to_xml(self):
        mt_node = etree.Element('master_theorem')
        for theorem in self.theorems:
            mt_node.append(theorem.to_xml())
        return mt_node


def generate_semantics_from_doc(doc, max_gen=1, use_gold_trees=False):
    """
    Returns string representations of logical formulas,
    as stored in the "sem" attribute of the root node
    of semantic trees.
    If a premise has no semantic representation, it is ignored.
    If there are no semantic representation at all, or the conclusion
    has no semantic representation, it returns None to signal an error.
    """
    sentences = doc.xpath('./sentences/sentence')
    # There are not enough correctly parsed sentences to form a theorem.
    if not sentences or len(sentences) < 2:
        return
    semantics_lists = []
    for sentence in sentences:
        semantics = sentence.xpath('./semantics')
        if use_gold_trees:
            try:
                gold_ind = int(sentence.get('gold_tree', 0))
            except:
                gold_ind = 0
            if 0 <= gold_ind < len(semantics):
                if semantics[gold_ind].get('status', 'failed') != 'success':
                    logging.warning(
                        'Requested gold_tree has a failed semantic parse: {0}\n{1}'
                        .format(sentence.attrib, semantics[gold_ind].attrib))
                semantics = [semantics[gold_ind]]
        semantics_lists.append(semantics)
    # Case: the conclusion has no semantic interpretations.
    if len(semantics_lists[-1]) == 0:
        return

    i = 0
    for sems in itertools.product(*semantics_lists):
        # from pudb import set_trace; set_trace()
        if i >= max_gen:
            return
        if any(sem.get('status', 'failed') != 'success' for sem in sems):
            continue
        if any(sem.xpath('./span[1]/@sem')[0] is None for sem in sems):
            continue
        i += 1
        yield sems
    if i == 0:
        logging.warning(
            'Cartesian product of semantic interpretations exhausted with i == 0'
        )
    return


def find_final_conclusion_sep_line_index(coq_output_lines):
    indices = [
        i for i, line in enumerate(coq_output_lines)
        if line.startswith('===') and line.endswith('===')
    ]
    if not indices:
        return None
    return indices[-1]


## for text similarity task
def get_subgoal_lines(coq_output_lines):
    ## ConclusionLines
    line_index_last_conclusion_sep = find_final_conclusion_sep_line_index(
        coq_output_lines)
    if not line_index_last_conclusion_sep:
        return None
    ## extract all subgoals
    subgoals = []
    subgoalflg = 0
    subgoals.append(coq_output_lines[line_index_last_conclusion_sep + 1])
    for line in coq_output_lines[line_index_last_conclusion_sep + 1:]:
        if subgoalflg == 1:
            subgoals.append(line)
            subgoalflg = 0
        if re.search("subgoal ", line):
            subgoalflg = 1
    return subgoals
