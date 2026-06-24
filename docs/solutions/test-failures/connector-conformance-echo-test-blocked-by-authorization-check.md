---
title: Connector conformance echo round-trip test blocked by authorization check
date: 2026-06-24
category: test-failures
module: connector conformance suite / connectors
problem_type: test_failure
component: testing_framework
symptoms:
  - "AssertionError: Expected 'mock' to have been called once. Called 0 times."
  - "test_echo_round_trip_contract[discord], [matrix], [xmpp] fail; telegram + loopback pass"
  - "Full suite on main: 3 failed, 198 passed (pre-existing)"
  - "is_authorized returns False because conversation_ref='chat' is not in config['channels'] and the test Envelope carries no raw guild/room state"
  - "ConnectorManager.dispatch persists the record but suppresses the reply for unauthorized inbound"
root_cause: test_isolation
resolution_type: test_fix
severity: medium
tags: [connector-conformance, echo-round-trip, is-authorized, authorization, test-isolation, parametrized-test, strangler-fig, mock-assertion]
---

# Connector conformance echo round-trip test blocked by authorization check

## Problem

The shared connector conformance suite (`tests/test_connector_conformance.py`) had three pre-existing failures on `main`. `test_echo_round_trip_contract[discord]`, `[matrix]`, and `[xmpp]` all failed because a cross-cutting authorization gate was added to those three connectors *after* the shared echo-routing contract was written, and the contract was never reconciled with the new gate.

The conformance contract exists to prove one thing for every platform: the echo **routing** chain is wired correctly — an inbound `Envelope` is dispatched to the default handler, which produces a reply, which is sent. It is deliberately uniform: the same test body runs against every connector via `@pytest.mark.parametrize('name', sorted(CONNECTOR_CLASSES))`. For each platform it builds a real `ConnectorManager`, registers the echo handler, stubs the persistence surfaces, dispatches `Envelope(name, 'user', 'chat', 'echo me')`, and asserts telegram never replies (strangler-fig arbitration pin) while every other connector replies exactly once with `reply.text == 'echo me'`.

Independently, discord/matrix/xmpp each grew an `is_authorized(envelope)` method, and `ConnectorManager.dispatch` was changed to persist the inbound message and then suppress the reply when the connector reports the conversation is unauthorized (observation kept, response gated). The conformance Envelope uses `conversation_ref='chat'` — which is in no connector's `channels` allowlist — and carries no `raw`, so it has no guild/room/type state to mark it a DM. For the three gated connectors `is_authorized` therefore returned `False`, dispatch returned before sending, and `send.assert_called_once()` failed. Mastodon and loopback have no gate, so they continued to pass.

## Symptoms

- Full suite on `main`: `3 failed, 198 passed`. Conformance file alone: `3 failed, 29 passed`.
- Failing tests: `test_echo_round_trip_contract[discord]`, `test_echo_round_trip_contract[matrix]`, `test_echo_round_trip_contract[xmpp]`.
- Identical failure output for each:

  ```
  AssertionError: Expected 'mock' to have been called once. Called 0 times.
  ```

- Mastodon and loopback parametrizations passed, which is the tell: only the three connectors that grew an `is_authorized` gate failed. The failures were pre-existing — they landed with the authorization feature, not with any new change under investigation.

## What Didn't Work

**Weakening or removing `is_authorized` on the connectors.** This would make the contract green by deleting the feature the connectors were built for — the separation of *observation* (always persisted) from *response* (gated to authorized channels/DMs). That regresses real behavior to satisfy a test. Wrong layer entirely.

**Giving the conformance Envelope an authorized `conversation_ref`** — e.g. adding `'chat'` to each connector's `channels` config, or fabricating `raw` guild/room/type state so each gate would pass. This couples the uniform shared contract to each connector's *different* `is_authorized` internals:

- discord reads `envelope.raw.guild` (DM when `None`);
- matrix queries `client.rooms` member count (DM when `member_count <= 2`);
- xmpp inspects the message type (DM when not `groupchat`).

To satisfy all three you would special-case three incompatible authorization implementations inside one test that is meant to be platform-agnostic. Brittle, and it drags an orthogonal concern back into the routing contract.

## Solution

Stub the new gate the same way the test already stubs persistence — neutralize it for the routing assertion. One line plus a comment, added just before `dispatch`:

```python
## This contract pins echo ROUTING (dispatch -> handler -> send), not
## authorization policy. Channel-gating connectors (discord/matrix/xmpp)
## would otherwise refuse to answer the unauthorized 'chat' conversation;
## their is_authorized behavior is covered by their own per-connector
## tests, so force-authorize here the same way persistence is stubbed out.
manager.connectors[name].is_authorized = lambda env: True
```

This sits alongside the existing isolation in the same test, which already replaces the persistence collaborators with mocks:

```python
monkeypatch.setattr(neutral, 'persist_envelope', AsyncMock())
monkeypatch.setattr(neutral, 'resolve_person', AsyncMock())
monkeypatch.setattr(chat_store, 'store_message', AsyncMock())
```

Authorization is treated as exactly the same kind of orthogonal collaborator: stubbed to a pass-through so the routing assertion measures routing only. After the fix the full suite is `201 passed`.

## Why This Works

`ConnectorManager.dispatch` gates replies through an optional connector hook:

```python
authorized = True
if hasattr(connector, 'is_authorized'):
    authorized = connector.is_authorized(envelope)
if not authorized:
    return
```

The conformance contract's job is to prove the echo routing chain (dispatch → default handler → send) is wired for each connector — *not* to exercise authorization policy. Authorization already has dedicated, focused coverage in the per-connector tests (`test_discord.py` covers `is_authorized` DM/allowed/denied; `test_matrix.py` and `test_xmpp.py` cover their own gates against real `raw`/room/type state). The shared contract should assert only what it owns; forcing `is_authorized → True` removes the gate from the path so the `send.assert_called_once()` assertion is testing routing in isolation. That is test isolation — separating two genuinely orthogonal concerns into the tests that own them — not papering over a defect. The product code is correct; the gate correctly refuses an unauthorized `'chat'` conversation. Only the contract needed to be told that gate is out of scope for it.

## Prevention

- **When you add a cross-cutting gate** (authorization, rate-limiting, a feature flag) to multiple implementations that sit behind a shared contract test, update that contract in the same change to neutralize the new concern — stub it true / pass-through — so the contract keeps asserting only the behavior it owns. Then cover the new gate with its own focused per-implementation tests.
- **Mirror the existing isolation.** A contract test that already monkeypatches some collaborators (persistence here) signals the right pattern: stub *newly added* collaborators the same way, rather than feeding the real gate satisfying-but-coupled fake state (`channels` entries, fabricated `raw`).
- **A pre-existing red suite on `main` is a signal**, not noise: a prior feature landed without reconciling a shared contract. Fix forward by separating concerns; don't weaken the feature to turn the suite green.

## Related Issues

- The same contract pins telegram to `send.assert_not_called()` because legacy aiogram handlers own Telegram replies — connector-path dispatch must not double-respond. The `is_authorized` stub and the telegram pin are two facets of the same principle: the routing contract isolates itself from concerns owned elsewhere (legacy handlers, authorization policy, persistence). See `docs/solutions/architecture-patterns/strangler-fig-dispatch-arbitration.md`.
- Observation-vs-response separation in `ConnectorManager.dispatch`: inbound messages are always persisted before the authorization check, so suppressing a reply never loses the observation. The per-connector `is_authorized` tests are the canonical coverage for that gate.
- `docs/solutions/logic-errors/discord-connector-logic-fixes-2026-06-16.md` — the source-side change that introduced `is_authorized()` and moved the check into `dispatch`; this learning is its test-side consequence.
- `docs/solutions/architecture-patterns/echo-everywhere-multi-connector-architecture-2026-06-12.md` — defines the "echo everywhere" guarantee the contract asserts (now policy-gated by `is_authorized`).
