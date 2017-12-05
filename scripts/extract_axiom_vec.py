#!/usr/bin/python3
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

import json
import glob
import re
import numpy as np
import collections
from collections import defaultdict
from subprocess import Popen
import subprocess
import sys
from abduction_tools import *
# Initial Q-value
#trial
Q = np.zeros((101,500))

LEARNING_COUNT = 100
GAMMA = 0.8
GOAL_STATE = 100
pred2id = collections.defaultdict(lambda: len(pred2id))
arg2id = collections.defaultdict(lambda: len(arg2id))

class QLearning(object):
    def __init__(self):
        print("init")
    
    def learn(self):
        # set a start state randomly
        state = self._getRandomState()
        for i in range(LEARNING_COUNT):        
            # extract possible actions in state
            possible_actions = self._getPossibleActionsFromState(state)
            
            # choise an action from possible actions randomly
            action = random.choice(possible_actions)        
            
            # Update Q-value
            # Q(s,a) = r(s,a) + Gamma * max[Q(next_s, possible_actions)]
            next_state = action # in this example, action value is same as next state
            next_possible_actions = self._getPossibleActionsFromState(next_state)
            max_Q_next_s_a = self._getMaxQvalueFromStateAndPossibleActions(next_state, next_possible_actions)
            Q[state, action] = R[state, action] + GAMMA * max_Q_next_s_a
            
            state = next_state
            
            # If an agent reached a goal state, restart an episode from a random start state
            if state == GOAL_STATE:
                state = self._getRandomState()
    
    def _getRandomState(self):
        return random.randint(0, R.shape[0] - 1)
      
    def _getPossibleActionsFromState(self, state):
        if state < 0 or state >= R.shape[0]: sys.exit("invaid state: %d" % state)
        return list(np.where(np.array(R[state] != -1)))[0]
    
    def _getMaxQvalueFromStateAndPossibleActions(self, state, possible_actions):
        return max([Q[state][i] for i in (possible_actions)])
            
    def dumpQvalue(self):
        print(Q.astype(int)) # convert float to int for redability

    def runGreedy(self, start_state = 0):
        print("===== START =====")
        state = start_state
        while state != GOAL_STATE:
            print("current state: %d" % state)
            possible_actions = self._getPossibleActionsFromState(state)
            
            # get best action which maximaizes Q-value(s, a)
            max_Q = 0
            best_action_candidates = []
            for a in possible_actions:            
                if Q[state][a] > max_Q:
                    best_action_candidates = [a,]
                    max_Q = Q[state][a]
                elif Q[state][a] == max_Q:
                    best_action_candidates.append(a)
            
            # get a best action from candidates randomly
            best_action = random.choice(best_action_candidates)
            print("-> choose action: %d" % best_action)
            state = best_action # in this example, action value is same as next state
        print("state is %d, GOAL!!" % state)

def extract_prem_preds(prems):
    prem_preds = []
    prem_args = []
    for prem in prems:
        if check_prem_decomposed(prem):
            prem_pred = prem.split()[2]
            prem_arg = prem.split()[3:]
            if prem_pred.startswith('_'):
                prem_preds.append(prem_pred)
                prem_args.append(prem_arg)
    prem_args = init_args(prem_args)
    return prem_preds, prem_args

def extract_subg_preds(subgs):
    subg_preds = []
    subg_args = []
    for subg in subgs:
        if check_subg_decomposed(subg):
            subg_pred = subg.split()[0]
            subg_arg = subg.split()[1:]
            if subg_pred.startswith('_'):
                subg_preds.append(subg_pred)
                subg_args.append(subg_arg)
    subg_args = init_args(subg_args)
    return subg_preds, subg_args

def check_prem_decomposed(line):
    if not line.startswith('H'):
        return False
    if re.search("forall", line):
        return False
    if re.search("exists", line):
        return False
    return True

def check_subg_decomposed(line):
    if not line.startswith('_'):
        return False
    if re.search("forall", line):
        return False
    if re.search("exists", line):
        return False
    return True

def convert_pred(preds):
    return [pred2id[pred] for pred in preds]

def convert_arg(args):
    return [arg2id[arg] for arg in args]

def init_args(subg_args):
    init_args = []
    ex2id = collections.defaultdict(lambda: len(ex2id))
    
    for subg_arg in subg_args:
        str_arg = " ".join(subg_arg)
        #initialize existential variables
        if re.search("\?", str_arg):
            ex_arg = re.search("(\?[0-9]*)", str_arg).group(1)
            pattern = "y"+str(ex2id[ex_arg])
            str_arg = re.sub("(\?[0-9]*)", pattern, str_arg)
        init_args.append(str_arg)
            
    return init_args

def extract_all_arg(prem_arg, sub_arg):
    prem_args = prem_arg.split()
    sub_args = sub_arg.split()
    prem_args = clean_args(prem_args)
    sub_args = clean_args(sub_args)
    all_args = list(set(prem_args+sub_args))
    return " ".join(all_args)

def clean_args(args):
    newargs = []
    for arg in args:
        if arg == "(Subj" or arg == "(Acc":
            continue
        else:
            newargs.append(re.sub("[\(\)]", '', arg))
    return newargs

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

def main():
    all_info = defaultdict(list)
    files = glob.glob("subgoal_results/sick_trial_*.err")
    for file in files[0:10]:
        f = open(file,"r")
        filename = re.search("sick_(trial_[0-9]*)\.", file).group(1)
        #print(filename)
        try:
            temp = {i : json.loads(line) for i, line in enumerate(f)}
        except:
            continue
        else:
            if temp:
                if "prem" in temp[0]:
                    coq_script = temp[0]["coq"]
                    prem_preds, prem_args = extract_prem_preds(temp[0]["prem"])
                    subg_preds, subg_args = extract_subg_preds(temp[0]["subg"])
                    all_info[filename].append(convert_pred(prem_preds))
                    all_info[filename].append(convert_arg(prem_args))
                    all_info[filename].append(convert_pred(subg_preds))
                    all_info[filename].append(convert_arg(subg_args))
                    all_info[filename].append(prem_preds)
                    all_info[filename].append(prem_args)
                    all_info[filename].append(subg_preds)
                    all_info[filename].append(subg_args)
                    all_info[filename].append(coq_script)
        
    for k, v in all_info.items():     
        prem_pred_vec = np.zeros(len(pred2id))
        prem_pred_vec.put(v[0], 1)
        prem_arg_vec = np.zeros(len(arg2id))
        prem_arg_vec.put(v[1], 1)
        subg_pred_vec = np.zeros(len(pred2id))
        subg_pred_vec.put(v[2], 1)
        subg_arg_vec = np.zeros(len(arg2id))
        subg_arg_vec.put(v[3], 1)
        #print(prem_pred_vec, prem_arg_vec, subg_pred_vec, subg_arg_vec)
        #create premise vector and subgoal vector(state)
        #feature: currently, wordID and argumentID(in trial dataset, dimension is about 1200)
        prem_vec = np.concatenate([prem_pred_vec, prem_arg_vec], axis=0)
        subg_vec = np.concatenate([subg_pred_vec, subg_arg_vec], axis=0)

        #action
        for prem in v[4]:
            for subg in v[6]:
                prem_arg = v[5][v[4].index(prem)]
                sub_arg = v[7][v[6].index(subg)]
                all_arg = extract_all_arg(prem_arg, sub_arg)
                axiom = "Axiom ax{0}{1} : forall {2}, {0} {3} -> {1} {4}.\n"\
                .format(prem,subg,all_arg,prem_arg,sub_arg)
                #attempt axiom injection
                coq_script = insert_axioms_in_coq_script(set([axiom]), v[8])
                process = Popen(
                    coq_script,
                    shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                output_lines = [
                    line.decode('utf-8').strip() for line in process.stdout.readlines()]
                conclusions = get_conclusion_lines(output_lines)
                #print(output_lines)
                if conclusions is None:
                    print("subgoal removed!")
                    #update the state
                elif len(conclusions) < len(v[6]):
                    print("subgoal removed!")
                    #update the state
                else:
                    print("subgoal not removed")
                    #update the state





if __name__ == '__main__':
    main()