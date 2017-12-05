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

from abduction_tools import *

class AxiomsSubgoal(object):
    """
    Extract premise + subgoal information
    """
    def __init__(self):
        pass

    def attempt(self, coq_scripts, context=None):
        return extract_all_subgoals(coq_scripts)

def extract_all_subgoals(coq_scripts):
    direct_proof_script = coq_scripts[0]
    reverse_proof_script = coq_scripts[1]
    premises, subgoals, coq_script_debug = extract_subgoals(direct_proof_script)
    #neg_premises, neg_subgoals, neg_coq_script_debug = extract_subgoals(reverse_proof_script)
    log = {"prem": premises,
           "subg": subgoals,
           #"neg_prem": neg_premises,
           #"neg_subg": neg_subgoals,
           "coq": coq_script_debug,
           #"neg_coq": neg_coq_script_debug
           }
    print(json.dumps(log), file=sys.stderr)
    return "unknown", []

def extract_subgoals(coq_script):
    current_tactics = get_tactics()
    debug_tactics = 'repeat nltac_base. try substitution. Qed'
    coq_script_debug = coq_script.replace(current_tactics, debug_tactics)
    process = Popen(
        coq_script_debug,
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output_lines = [line.decode('utf-8').strip()
                    for line in process.stdout.readlines()]
    premises = get_premise_lines(output_lines)
    subgoals = get_conclusion_lines(output_lines)
    if not premises or not subgoals:
        failure_log = {"type error": has_type_error(output_lines),
                       "open formula": has_open_formula(output_lines)}
        print(json.dumps(failure_log), file=sys.stderr)
    return premises, subgoals, coq_script_debug

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
        elif re.search("No more subgoals", line):
            conclusion_lines.append(line)
        elif re.search("subgoal", line):
            continue
        elif re.search('repeat nltac_base', line):
            return conclusion_lines
        else:
            conclusion_lines.append(line)
    return conclusion_lines
