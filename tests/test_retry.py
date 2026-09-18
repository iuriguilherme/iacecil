"""Conflict retry, shared by the neutral and chat stores.

Consolidating every chat of a bot into one storage raises BTree
contention, so the retry is what keeps concurrent writers from losing
records. It had no direct coverage.
"""

import pytest
from ZODB.POSException import ConflictError

from iacecil.controllers.persistence.retry import (
    MAX_COMMIT_RETRIES,
    commit_with_retry,
)


def test_a_transaction_that_succeeds_runs_once():
    calls = []

    def write(value):
        calls.append(value)
        return 'msg-1'

    assert commit_with_retry(write, 'record') == 'msg-1'
    assert calls == ['record']


def test_a_conflict_is_retried_until_it_commits():
    """Two writers racing on one chat container: the loser re-runs and
    finds the winner's work."""
    attempts = {'n': 0}

    def write():
        attempts['n'] += 1
        if attempts['n'] < 3:
            raise ConflictError()
        return 'msg-1'

    assert commit_with_retry(write) == 'msg-1'
    assert attempts['n'] == 3


def test_an_unresolvable_conflict_is_raised_not_swallowed():
    """A conflict surviving every attempt is a real failure; the caller
    buffers or logs it rather than believing the write landed."""
    attempts = {'n': 0}

    def always_conflicts():
        attempts['n'] += 1
        raise ConflictError()

    with pytest.raises(ConflictError):
        commit_with_retry(always_conflicts)
    assert attempts['n'] == MAX_COMMIT_RETRIES


def test_other_exceptions_are_not_retried():
    """Only a conflict is worth re-running; anything else is surfaced
    immediately so the write buffer can hold the record."""
    attempts = {'n': 0}

    def fails(): 
        attempts['n'] += 1
        raise ValueError('not a conflict')

    with pytest.raises(ValueError):
        commit_with_retry(fails)
    assert attempts['n'] == 1


def test_arguments_reach_the_transaction_on_every_attempt():
    seen = []

    def write(db, msg_id, record):
        seen.append((db, msg_id, record))
        if len(seen) < 2:
            raise ConflictError()
        return msg_id

    assert commit_with_retry(write, 'db', 'msg-1', {'text': 'hi'}) == 'msg-1'
    assert seen == [('db', 'msg-1', {'text': 'hi'})] * 2
