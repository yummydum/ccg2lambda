from collections import defaultdict
import re

from abduction_tools import parse_coq_line
from tree_tools import is_string

def get_tree_pred_args(line, is_conclusion=False):
    """
    Given the string representation of a premise, where each premise is:
      pX : predicate1 (arg1 arg2 arg3)
      pY : predicate2 arg1
    or the conclusion, which is of the form:
      predicate3 (arg2 arg4)
    returns the list  of variables (tree leaves).
    """
    tree_args = None
    if not is_conclusion:
        tree_args = parse_coq_line(' '.join(line.split()[2:]))
    else:
        tree_args = parse_coq_line(line)
    if tree_args is None or is_string(tree_args) or len(tree_args) < 1:
        return None
    return [l for l in tree_args.leaves() if l != '=']

def contains_case(coq_line):
    """
    Returns True if the coq_line contains a case predicate, e.g.
    'H0 : _meat (Acc x1)'
    'H : _lady (Subj x1)'
    Returns False otherwise.
    We assume that case is specified by an uppercase character
    followed by at least two lowercased characters, e.g. Acc, Subj, Dat, etc.
    """
    if re.search(r'[A-Z][a-z][a-z]', coq_line):
        return True
    return False

def make_phrases_from_premises_and_conclusions(premises, conclusions):
    premises = [p for p in premises if not contains_case(p) and p.split()[2].startswith('_')]

    p_pred_args = {}
    for p in premises:
        predicate = p.split()[2]
        args = get_tree_pred_args(p, is_conclusion=False)
        if args is not None:
            p_pred_args[predicate] = args

    c_pred_args = {}
    for c in conclusions:
        predicate = c.split()[0]
        args = get_tree_pred_args(c, is_conclusion=True)
        if args is not None:
            c_pred_args[predicate] = args

    # Compute relations between arguments as frozensets.
    c_args_preds = defaultdict(set)
    for pred, args in c_pred_args.items():
        for arg in args:
            c_args_preds[frozenset([arg])].add(pred)
        c_args_preds[frozenset(args)].add(pred)
    # from pudb import set_trace; set_trace()
    for args, preds in sorted(c_args_preds.items(), key=lambda x: len(x[0])):
        for targs, _ in sorted(c_args_preds.items(), key=lambda x: len(x[0])):
            if args.intersection(targs):
                c_args_preds[targs].update(preds)

    exclude_preds_in_conclusion = {l.split()[0] for l in conclusions if contains_case(l)}

    axioms = set()
    phrase_pairs = []
    for args, c_preds in c_args_preds.items():
        c_preds = sorted([
            p for p in c_preds if p.startswith('_') and p not in exclude_preds_in_conclusion])
        if len(args) > 1:
            premise_preds = [p for p, p_args in p_pred_args.items() if set(p_args).issubset(args)]
            premise_preds = sorted([p for p in premise_preds if not contains_case(p)])
            if premise_preds:
                phrase_pairs.append((premise_preds, c_preds)) # Saved phrase pairs for Yanaka-san.
                premise_pred = premise_preds[0]
                for p in c_preds:
                    c_num_args = len(c_pred_args[p])
                    p_num_args = len(p_pred_args[premise_pred])
                    axiom = 'Axiom ax_phrase{0}{1} : forall {2} {3}, {0} {2} -> {1} {3}.'.format(
                        premise_pred,
                        p,
                        ' '.join('x' + str(i) for i in range(p_num_args)),
                        ' '.join('y' + str(i) for i in range(c_num_args)))
                    axioms.add(axiom)
    # print(phrase_pairs) # this is a list of tuples of lists.
    return axioms

# def estimate_existential_variables(premises, conclusions):
#     #to do: check existential variables in subgoals and estimate the best variable
#     # estimate by number of arguments, case, lexical knowledge??
#     # substitute estimated variables for existential variables
#     # print("premises:{0}, conclusions:{1}".format(premises, conclusions), file=sys.stderr)
#     # conclusions = [c for c in conclusions if c.split()[0].startswith('_')]
#     args_to_preds = cluster_args(premises, conclusions)
#     return set()
