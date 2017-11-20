#!/usr/bin/python3
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

import unittest

from abduction_phrase_p import make_phrases_from_premises_and_conclusions

class EstimateExistentialVariablesTestCase(unittest.TestCase):
    def test_cut_into_piece(self):
        premises = [
            'H0 : _meat (Acc x1)',
            'H : _lady (Subj x1)',
            'H2 : _cut x1',
            'H6 : _up x1',
            'H5 : _precisely x1',
            'H4 : True',
            'x1 : Event',
            'H3 : True',
            'H1 : True']
        conclusions = [
            '_piece ?775',
            '_into x1 ?775',
            '_woman (Subj x1)']
        expected_axioms = set([
            'Axiom ax_phrase_cut_into : forall x0 y0 y1, _cut x0 -> _into y0 y1.',
            'Axiom ax_phrase_cut_piece : forall x0 y0, _cut x0 -> _piece y0.'])
        axioms = make_phrases_from_premises_and_conclusions(premises, conclusions)
        self.assertEqual(expected_axioms, axioms,
            msg="{0} vs. {1}".format(expected_axioms, axioms))

    def test_protective_gear(self):
        premises = [
            'H1 : True',
            'x0 : Event',
            'H3 : True',
            'H0 : _equip x0',
            'x1 : Entity',
            'H6 : _with x0 x1',
            'H7 : True',
            'H4 : _protective x1',
            'H8 : _gear x1',
            'H10 : True',
            'H : Acc x0 = Acc x0',
            'H2 : _people (Acc x0)']
        conclusions = [
            '_use ?4844',
            'Acc ?4844 = x1',
            '_protection ?5065',
            '_for ?4844 ?5065']
        expected_axioms = set([
            'Axiom ax_phrase_gear_use : forall x0 y0, _gear x0 -> _use y0.',
            'Axiom ax_phrase_gear_protection : forall x0 y0, _gear x0 -> _protection y0.',
            'Axiom ax_phrase_gear_for : forall x0 y0 y1, _gear x0 -> _for y0 y1.'])
        axioms = make_phrases_from_premises_and_conclusions(premises, conclusions)
        self.assertEqual(expected_axioms, axioms,
            msg="{0} vs. {1}".format(expected_axioms, axioms))

    def test_sidewalk(self):
        premises = [
            'H1 : _skip x1',
            'H2 : _on x1 x2',
            'H3 : _sidewalk x2',
            'H4 : _girl (Subj x1)',
            'H5 : _rope (Acc x1)']
        conclusions = [
            '_street ?2961',
            '_near x1 ?2961']
        expected_axioms = set([
            'Axiom ax_phrase_skip_street : forall x0 y0, _skip x0 -> _street y0.',
            'Axiom ax_phrase_skip_near : forall x0 y0 y1, _skip x0 -> _near y0 y1.'])
        # from pudb import set_trace; set_trace()
        axioms = make_phrases_from_premises_and_conclusions(premises, conclusions)
        self.assertEqual(expected_axioms, axioms,
            msg="{0} vs. {1}".format(expected_axioms, axioms))

if __name__ == '__main__':
    suite1 = unittest.TestLoader().loadTestsFromTestCase(EstimateExistentialVariablesTestCase)
    suites = unittest.TestSuite([suite1])
    unittest.TextTestRunner(verbosity=2).run(suites)
