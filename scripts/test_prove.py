from prove import main
import pytest


def test_prove_1(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_1.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The kids are boys'
    assert theorem.result2 == "entailment"
    return


# should be contradiction but golden is wrong
def test_prove_2(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_2.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert theorem.inference_result
    assert theorem.result2 == 'contradiction'
    return


@pytest.mark.skip("smile_e2")
def test_prove_3(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_3.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[2] == 'The boys are kids'
    assert axioms[0] == 'The man is with a smile'  # nice
    assert axioms[1] == 'The boys are near a man'  # nice
    theorem.result2 == "entailment"
    return


def test_prove_5(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_5.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[1] == 'The man is old'
    assert axioms[2] == 'The man is standing'
    assert axioms[3] == 'The man is in a background'
    assert axioms[0] == 'The kids are in a yard'
    return


def test_prove_12(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_12.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The dogs are a hugging'  # wrong pos
    assert axioms[1] == 'The dogs are wrestling'
    return


def test_prove_26(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_26.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[1] == 'The bicycle is tricks'
    assert axioms[3] == 'The wheel is a motorbike'
    assert axioms[4] == 'The person is a man'
    assert axioms[2] == 'The person is doing tricks'
    assert axioms[0] == 'The person is in a jacket'  # where did black go?
    return


def test_prove_40(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        ['scripts/prove.py', 'data/parsed/pair_40.sem.xml', '--write'])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The player is with a jersey'
    assert axioms[1] == 'The basketball is a ball'  # composite word
    assert axioms[2] == 'The basketball is a game'
    assert axioms[3] == 'The player is at a basketball'
    assert axioms[4] == 'The player is a man'  # no

    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_40.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The player is with a jersey'
    assert axioms[1] == 'The basketball is a ball'  # composite word
    assert axioms[2] == 'The basketball is a game'
    assert axioms[3] == 'The player is at a basketball'
    assert axioms[4] == 'The player is a man'  # no
    return


# CONTRADICTION by negation
def test_prove_42(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_42.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    theorem = main()
    assert theorem.inference_result
    assert theorem.result2 == 'contradiction'
    return


# negation removed NEUTRAL
def test_prove_47(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_47.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The people are young'
    assert axioms[3] == 'The people are women'
    assert axioms[1] == 'The people are sparring'
    assert axioms[2] == 'The people are in a fight'  # how about kick boxing?
    return


def test_prove_90(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_90.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The pool is full'  # contradiction label
    # assert theorem.result2 == "contradiction"
    return


def test_prove_100(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_100.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The girls are doing backbends outdoors'
    theorem.result2 == "entailment"
    return


def test_prove_122(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_122.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The kid is a none'  # wrong
    return


def test_prove_129(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_129.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert theorem.inference_result
    return


def test_prove_140(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_140.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert theorem.inference_result
    return


def test_prove_141(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        ['scripts/prove.py', 'data/parsed/pair_141.sem.xml', '--write'])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert theorem.inference_result
    return


def test_prove_150(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        ['scripts/prove.py', 'data/parsed/pair_141.sem.xml', '--write'])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert theorem.inference_result
    return


def test_prove_161(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_161.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert theorem.inference_result
    return


def test_prove_186(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_186.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The crowd is asian'
    assert axioms[1] == 'The crowd is at various'  # ?
    assert axioms[2] == 'The crowd is large'
    return


def test_prove_254(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_254.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert theorem.inference_result
    return


# CONTRADICTION with subgoal
def test_prove_276(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_276.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The boy is through blue'
    assert axioms[1] == 'The boy is wading'
    return


def test_prove_1135(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_1135.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The turtle is hunting a fish'
    assert axioms[1] == 'The turtle is for a food'
    assert axioms[2] == 'The turtle is a sea'
    return


def test_prove_1161(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_1161.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[1] == 'The eggs are ingredients'
    assert axioms[0] == 'The woman is adding ingredients to a bowl'
    return


def test_prove_1000(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_1000.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The boy is lowering a eyebrow'
    assert axioms[1] == 'The boy is facing a eyebrow'
    assert axioms[2] == 'The boy is behind blue'  # composite word in_front_of
    assert axioms[3] == 'The eyebrow is a camera'
    return


@pytest.mark.skip
def test_prove_10000(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_10000.sem.xml',
        '--write',
    ])
    # No match at all!
    theorem = main()
    axioms = theorem.readable_subgoals
    return


@pytest.mark.skip("race_e2")
def test_prove_1010(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_1010.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The jockeys is racing'
    assert axioms[1] == 'The jockeys is on a field'
    assert axioms[2] == 'The jockeys is racing a field'
    return


@pytest.mark.skip("racer -> sematic role")
def test_prove_1016(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_1016.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The grass is a field'
    assert axioms[1] == 'The racers are jockeys'
    assert axioms[2] == 'The racers are racing'
    assert axioms[3] == 'The racers are yelling horses'
    return


def test_prove_1212(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_1212.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'There are two woman'
    assert axioms[2] == 'The woman is boys'
    assert axioms[1] == 'The device is a phone'
    return


def test_prove_232(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        ['scripts/prove.py', 'data/parsed/pair_232.sem.xml', '--write'])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert theorem.inference_result
    return


# contradicion with subgoal
def test_prove_2350(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_2350.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The lady is removing a cheese to a sauce'
    assert axioms[1] == 'The lady is from a sauce'
    assert axioms[2] == 'The lady is a woman'

    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_2350.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    assert axioms[0] == 'The lady is removing a cheese to a sauce'
    assert axioms[1] == 'The lady is from a sauce'
    return


def test_prove_2763(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_2350.sem.xml',
        '--write',
    ])
    theorem = main()
    axioms = theorem.readable_subgoals
    # wrong preposition for dative
    assert axioms[0] == 'The lady is removing a cheese to a sauce'
    assert axioms[1] == 'The lady is from a sauce'  # from がここに来ちゃうか
    assert axioms[2] == 'The lady is a woman'


# where did vidio go?
# -> composite noun case...
# def test_prove_2634():
#     return

# why not provable?
# CCG tag diffrent... however may be possible to solve via axiom injection
# def test_prove_1694():
#     return

# def test_prove_975():
#     return

# def test_prove_9760():
#     return

# def test_prove_9148():
#     return

# test split 2152,
