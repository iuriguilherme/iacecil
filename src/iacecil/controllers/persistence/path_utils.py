"""Filesystem-safe path components, valid simultaneously on HFS+,
NTFS, ext4 and btrfs.

Platform-native identifiers (XMPP JIDs, Matrix room ids like
``!AbC:server.org``, Telegram chat ids) become storage path components.
The encoding is deterministic and injective so two distinct identifiers
can never share a path, including on case-insensitive filesystems
(HFS+, NTFS): uppercase letters are percent-encoded rather than
lowercased, and a literal ``%`` in the input is itself encoded so
encoded output never collides with raw input.
"""

SAFE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789._-")

## NTFS reserves these basenames case-insensitively, with or without
## an extension ("con.fs" included). Uppercase forms are already
## neutralized by the encoding; the guard below catches the lowercase
## forms that pass the allowlist verbatim.
NTFS_RESERVED = frozenset(
    ['con', 'prn', 'aux', 'nul']
    + [f'com{i}' for i in range(1, 10)]
    + [f'lpt{i}' for i in range(1, 10)]
)


def _encode_char(ch: str) -> str:
    return ''.join('%{:02x}'.format(b) for b in ch.encode('utf-8'))


def sanitize_component(value) -> str:
    """Encode one path component. Injective; reversible via
    desanitize_component()."""
    text = str(value)
    if not text:
        ## Bare '%' is unreachable by encoding (every generated '%' is
        ## followed by two hex digits), so it is a safe empty sentinel.
        return '%'
    encoded = ''.join(
        ch if ch in SAFE_CHARS else _encode_char(ch) for ch in text)
    ## '.' and '..' (and any all-dots name) are path navigation on
    ## every filesystem; encode the leading dot.
    if set(encoded) == {'.'}:
        encoded = _encode_char('.') + encoded[1:]
    ## NTFS reserved device names apply to the stem before the first
    ## dot and survive any extension appended later (e.g. '.fs').
    stem = encoded.split('.', 1)[0]
    if stem in NTFS_RESERVED:
        encoded = _encode_char(encoded[0]) + encoded[1:]
    return encoded


def desanitize_component(component: str) -> str:
    """Reverse sanitize_component()."""
    if component == '%':
        return ''
    out = bytearray()
    i = 0
    while i < len(component):
        if component[i] == '%':
            out.append(int(component[i + 1:i + 3], 16))
            i += 3
        else:
            out.extend(component[i].encode('ascii'))
            i += 1
    return out.decode('utf-8')
