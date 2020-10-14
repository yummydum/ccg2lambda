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
    assert axioms[0] == 'The young boy is a kid'
    assert axioms[1] == 'The man is smiling nearby with a smile_2'
    assert axioms[2] == 'The young boy is playing outdoors near a man'
    return


def test_prove_5(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_5.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms = main()
    assert axioms[0] == 'The young boy is a kid'
    assert axioms[1] == 'The man is smiling nearby with a smile_2'
    assert axioms[2] == 'The young boy is playing outdoors near a man'
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
    assert axioms[3] == 'The person is doing a trick in a black jacket'
    return


def test_prove_40(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_40.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms = main()
    assert axioms[0] == 'The basketball is a ball game'
    assert axioms[1] == 'The player is a man'
    assert axioms[
        2] == 'The player is dunking a basketball with a jersey at a ball game'
    return


def test_prove_186(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_186.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms = main()
    assert axioms[0] == 'The purple crowd people is a large asian'
    assert axioms[
        1] == 'The purple crowd people is eatting at a various red restaurant table'
    return


def test_prove_1135(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_1135.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms = main()
    assert axioms[0] == 'The turtle is a sea'
    assert axioms[1] == 'The turtle is huntting a fish for a food'
    return


def test_prove_1161(monkeypatch):
    monkeypatch.setattr('sys.argv', [
        'scripts/prove.py', 'data/parsed/pair_1161.sem.xml', '--write',
        '--abduction', 'spsa'
    ])
    axioms = main()
    assert axioms[0] == 'The egg is a ingredient'
    assert axioms[1] == 'The woman is adding a ingredient to a bowl '
    return
