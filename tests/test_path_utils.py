import re
import pytest

from iacecil.controllers.persistence.path_utils import (
    NTFS_RESERVED,
    desanitize_component,
    sanitize_component,
)

## Every encoded component must use only this alphabet — legal on
## HFS+, NTFS, ext4 and btrfs, and case-collision-free.
LEGAL = re.compile(r'^[a-z0-9._%-]+$')

SAMPLES = [
    'user@host.org',        # xmpp jid
    '!AbC:server.org',      # matrix room id (':' illegal on NTFS)
    '-1001234',             # telegram group id
    'con', 'nul', 'com1',   # lowercase NTFS reserved names
    '',                     # empty
    '.', '..',              # dot-only
    'Room', 'room',         # case pair (HFS+/NTFS case-insensitive)
    '%41', 'A',             # escape-char injectivity vs uppercase
    'a%2f',                 # literal percent in input
    '../../../etc',         # traversal-shaped input
    'côñ',                  # non-ascii
]


@pytest.mark.parametrize('value', SAMPLES)
def test_components_legal(value):
    encoded = sanitize_component(value)
    assert LEGAL.match(encoded), encoded
    ## Never a navigation name, never an NTFS reserved stem
    assert set(encoded) != {'.'}
    assert encoded.split('.', 1)[0] not in NTFS_RESERVED
    assert '/' not in encoded and '\\' not in encoded


@pytest.mark.parametrize('value', SAMPLES)
def test_round_trip(value):
    assert desanitize_component(sanitize_component(value)) == value


def test_injective_across_samples():
    encoded = [sanitize_component(v) for v in SAMPLES]
    assert len(set(encoded)) == len(SAMPLES)


def test_case_pair_distinct():
    assert sanitize_component('Room') != sanitize_component('room')


def test_percent_literal_never_collides_with_encoding():
    ## '%41' as input must not decode-collide with 'A' as input
    assert sanitize_component('%41') != sanitize_component('A')


def test_reserved_with_extension_guarded():
    ## 'con.fs'-shaped components are also NTFS-reserved
    encoded = sanitize_component('con.backup')
    assert encoded.split('.', 1)[0] not in NTFS_RESERVED
    assert desanitize_component(encoded) == 'con.backup'
