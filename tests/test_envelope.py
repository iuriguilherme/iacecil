import pytest
from iacecil.models.envelope import Envelope
from dataclasses import FrozenInstanceError

def test_envelope_frozen():
    env = Envelope("telegram", "sender1", "conv1", "Hello")
    with pytest.raises(FrozenInstanceError):
        env.text = "modified"

def test_envelope_defaults():
    env = Envelope("xmpp", "sender2", "conv2", "Test")
    assert env.reply_ref is None
    assert env.tags == set()
    assert env.raw is None
    assert env.extra == {}