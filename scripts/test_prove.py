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
    assert axioms[1] == 'The man is with a smile'
    assert axioms[2] == 'The young boy is playing outdoors near a man'
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
    assert axioms[4] == 'The player is dunking at a basketball'
    return
