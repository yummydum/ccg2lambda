from prove import main
import pytest


def test_prove_1(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_1.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The kids are boys'
    return


# should be contradiction but golden is wrong
def test_prove_2(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_2.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert is_proved
    return


# good example our method solves
def test_prove_3(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_3.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The boys are kids'
    assert axioms[1] == 'The man is with a smile_2'  # nice
    assert axioms[2] == 'The boys are near a man'  # nice
    return


def test_prove_5(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_5.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The man is old'
    assert axioms[1] == 'The man is standing'
    assert axioms[2] == 'The man is in a background'
    assert axioms[3] == 'The kids are in a yard'
    return


def test_prove_12(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_12.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The dogs are a hugging'  # wrong pos
    assert axioms[1] == 'The dogs are wrestling'
    return


def test_prove_26(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_26.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The bicycle is tricks'
    assert axioms[1] == 'The wheel is a motorbike'
    assert axioms[2] == 'The person is a man'
    assert axioms[3] == 'The person is doing tricks'
    assert axioms[4] == 'The person is in a black jacket'
    return


def test_prove_40(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        ['scripts/prove.py', 'data/parsed/pair_40.sem.xml', '--write'])
    axioms, is_proved = main()
    assert axioms[0] == 'The basketball is a ball'  # composite word
    assert axioms[1] == 'The basketball is a game'
    assert axioms[2] == 'The player is a man'  # no
    assert axioms[3] == 'The player is with a jersey'
    assert axioms[4] == 'The player is at a basketball'

    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_40.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The player is a man'
    assert axioms[1] == 'The player is with a jersey'  # good example
    assert axioms[2] == 'The player is at a basketball'  # good example
    return


def test_prove_42(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_42.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    return


def test_prove_47(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_47.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The people are young'
    assert axioms[1] == 'The people are women'
    assert axioms[2] == 'The people are sparring'
    assert axioms[3] == 'The people are in a kickboxing fight'  # false
    return


def test_prove_55(monkeypatch):
    """
    Test if abduction is working
    """
    monkeypatch.setattr(
        'sys.argv',
        ['scripts/prove.py', 'data/parsed/pair_55.sem.xml', '--write'])
    axioms, is_proved = main()
    assert not is_proved

    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_55.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert is_proved
    return


def test_prove_100(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_100.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    breakpoint()
    return


def test_prove_122(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_122.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The kid is a none'  # wrong
    return


def test_prove_129(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_129.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert is_proved
    return


def test_prove_140(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_140.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert is_proved
    return


def test_prove_141(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        ['scripts/prove.py', 'data/parsed/pair_141.sem.xml', '--write'])
    axioms, is_proved = main()
    assert is_proved
    return


def test_prove_150(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        ['scripts/prove.py', 'data/parsed/pair_141.sem.xml', '--write'])
    axioms, is_proved = main()
    assert is_proved
    return


def test_prove_161(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_161.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert is_proved
    return


def test_prove_186(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_186.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The people are asian'
    assert axioms[1] == 'The people are large'
    assert axioms[2] == 'The people are at a tables'
    return


def test_prove_254(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_254.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert is_proved
    return


def test_prove_1135(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_1135.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The turtle is a sea'
    assert axioms[1] == 'The turtle is hunting a fish'
    assert axioms[2] == 'The turtle is for a food'
    return


def test_prove_1161(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_1161.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The eggs are ingredients'
    assert axioms[1] == 'The woman is adding ingredients to a bowl'
    return


def test_prove_1000(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_1000.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The boy is lowering a camera'
    assert axioms[1] == 'The boy is facing a camera'
    assert axioms[
        2] == 'The boy is behind a front'  # composite word in_front_of
    return


def test_prove_10000(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_10000.sem.xml',
        '--write',
    ])
    # No match at all!
    axioms, is_proved = main()
    return


def test_prove_1010(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_1010.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The jockeys is racing'
    assert axioms[1] == 'The jockeys is on a field'
    assert axioms[2] == 'The jockeys is racing a field'
    return


def test_prove_1016(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_1016.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The grass is a field'
    assert axioms[1] == 'The racers are jockeys'
    assert axioms[2] == 'The racers are racing'
    assert axioms[3] == 'The racers are yelling horses'
    return


def test_prove_232(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        ['scripts/prove.py', 'data/parsed/pair_232.sem.xml', '--write'])
    axioms, is_proved = main()
    assert is_proved
    return


def test_prove_2350(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py',
        'data/parsed/pair_2350.sem.xml',
        '--write',
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The lady is a woman'
    assert axioms[1] == 'The lady is removing a cheese to a sauce'
    assert axioms[2] == 'The lady is from a sauce'

    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_2350.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The lady is removing a cheese to a sauce'
    assert axioms[1] == 'The lady is from a sauce'
    return


# def test_prove_975():
#     return

# def test_prove_9760():
#     return

# def test_prove_9148():
#     return

# lexical contradiction is not handled now!