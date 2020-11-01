from prove import main
import pytest


def test_prove_1(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_1.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms = main()
    assert axioms[0] == 'The kid is a boy'
    return


def test_prove_3(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_3.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms = main()
    assert axioms[0] == 'The boy is a kid'
    assert axioms[1] == 'The man is with a smile_2'
    assert axioms[2] == 'The boy is near a man'
    return


def test_prove_5(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_5.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms = main()
    assert axioms[0] == 'The man is old'
    assert axioms[1] == 'The man is standing'
    assert axioms[2] == 'The man is in_2 a background'
    assert axioms[3] == 'The kid is in a yard'
    return


def test_prove_26(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_26.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms = main()
    assert axioms[0] == 'The bicycle is a trick'
    assert axioms[1] == 'The wheel is a motorbike'
    assert axioms[2] == 'The person is a man'
    assert axioms[3] == 'The person is doing a trick'
    assert axioms[4] == 'The person is in a black jacket'
    return


def test_prove_40(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_40.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms = main()
    assert axioms[0] == 'The basketball is a ball'
    assert axioms[1] == 'The basketball is a game'
    assert axioms[2] == 'The player is a man'
    assert axioms[3] == 'The player is with a jersey'
    # assert axioms[4] == 'The player is with a jersey at a ball game'
    return


def test_prove_186(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_186.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms = main()
    assert axioms[0] == 'The people is asian'
    assert axioms[1] == 'The people is large'
    assert axioms[2] == 'The people is at a table'
    return


def test_prove_1135(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_1135.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms = main()
    assert axioms[0] == 'The turtle is a sea'
    assert axioms[1] == 'The turtle is huntting a fish'
    assert axioms[2] == 'The turtle is for a food'
    return


def test_prove_1161(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_1161.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms = main()
    assert axioms[0] == 'The egg is a ingredient'
    assert axioms[1] == 'The woman is adding a ingredient to a bowl'
    return


# def test_prove_1010(monkeypatch):
#     monkeypatch.setattr('sys.argv', [
#         'scripts/prove.py', 'data/parsed/pair_1010.sem.xml', '--write',
#         '--abduction', 'spsa'
#     ])
#     axioms = main()
#     assert axioms[0] == ''
#     assert axioms[1] == ''
#     return
