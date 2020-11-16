from prove import main
import pytest


def test_prove_1(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_1.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The kids is a boys'
    return


def test_prove_2(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_2.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The house is a yard'
    assert axioms[1] == 'The house is a background'
    assert axioms[2] == 'The children is a man'
    assert axioms[3] == 'The children is old'
    assert axioms[4] == 'The children is a kids'
    assert axioms[5] == 'The children is standing'
    # should be 'The man is old'
    return


def test_prove_3(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_3.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The boys is a kids'
    assert axioms[1] == 'The man is with a smile_2'
    assert axioms[2] == 'The boys is near a man'
    return


def test_prove_5(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_5.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The man is old'
    assert axioms[1] == 'The man is standing'
    assert axioms[2] == 'The man is in_2 a background'
    assert axioms[3] == 'The kid is in a yard'
    return


def test_prove_5(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_12.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The dogs is hugging'
    assert axioms[1] == 'The dogs is wrestling'
    return


def test_prove_26(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_26.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The bicycle is a tricks'
    assert axioms[1] == 'The wheel is a motorbike'
    assert axioms[2] == 'The person is a man'
    assert axioms[3] == 'The person is doing a tricks'
    assert axioms[4] == 'The person is in a black jacket'
    return


def test_prove_40(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_40.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The basketball is a ball'  # composite word
    assert axioms[1] == 'The basketball is a game'
    assert axioms[2] == 'The player is a man'
    assert axioms[3] == 'The player is with a jersey'
    # assert axioms[4] == 'The player is with a jersey at a ball game'
    return


def test_prove_42(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_42.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    breakpoint()
    return


def test_prove_47(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_47.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The people is young'
    assert axioms[1] == 'The people is a women'
    assert axioms[2] == 'The people is sparing'
    assert axioms[3] == 'The people is in a kickboxing fight'  # false
    return


def test_prove_100(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_100.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    breakpoint()
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
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_141.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert is_proved
    return


def test_prove_161(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_161.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert is_proved
    return


def test_prove_186(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_186.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The people is asian'
    assert axioms[1] == 'The people is large'
    assert axioms[2] == 'The people is at a tables'
    return


def test_prove_254(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_254.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert is_proved
    return


def test_prove_1135(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_1135.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The turtle is a sea'
    assert axioms[1] == 'The turtle is huntting a fish'
    assert axioms[2] == 'The turtle is for a food'
    return


def test_prove_1161(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_1161.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The eggs is a ingredients'
    assert axioms[1] == 'The woman is adding a ingredients to a bowl'
    return


def test_prove_1000(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_1000.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The boy is lowering a camera'
    assert axioms[1] == 'The boy is facing a camera'
    assert axioms[
        2] == 'The boy is behind a front'  # composite word in_front_of
    return


def test_prove_10000(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_10000.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    # No match at all!
    axioms, is_proved = main()
    return


def test_prove_1010(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_1010.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The jockeys is race_2ing'
    assert axioms[1] == 'The jockeys is on a field'
    assert axioms[2] == 'The jockeys is race_2ing a field'
    return


def test_prove_1016(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_1016.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The grass is a field'
    assert axioms[1] == 'The racers is a jockeys'
    assert axioms[2] == 'The racers is racing'
    assert axioms[3] == 'The racers is yelling a horses'
    return


def test_prove_232(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_232.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The kids is dance_2ing'
    return


def test_prove_2350(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_2350.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms, is_proved = main()
    assert axioms[0] == 'The lady is a woman'
    assert axioms[1] == 'The lady is removing a cheese to a sauce'
    assert axioms[2] == 'The lady is from a sauce'
    return


def test_prove_975():
    return


def test_prove_9760():
    return


def test_prove_9148():
    return


# lexical contradiction is not handled now!