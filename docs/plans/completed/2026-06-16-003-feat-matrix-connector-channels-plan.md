# Create Technical Plan

## Feature Description

Add channel configuration support to the Matrix connector, making it consistent with Discord and XMPP. The echo plugin is used to test. Need to update bot config and the instance example.

## Requirements

- R1. Matrix configuration should include a `channels` key (list of authorized room IDs).
- R2. Matrix connector should only reply to messages in rooms listed in `channels`, or in 1:1 DMs (rooms with <= 2 members).
- R3. Default configurations in `src/iacecil/config.py` and `docs/instance.example/bots/default.py` must be updated to include the new `channels` key for Matrix.

## Scope Boundaries

- Only the Matrix connector is affected.
- Testing will be done using the `echo` plugin.

## Key Technical Decisions

- **DM Detection in Matrix**: Unlike Discord (`message.guild`) or XMPP (`message.type == 'groupchat'`), Matrix events don't explicitly carry the DM vs group state in the text message event itself. We will use `self.client.rooms.get(envelope.conversation_ref)` to access the room state and check its member count (`len(room.users) <= 2`) to identify 1:1 DMs and always authorize them.

## Implementation Units

- U1. **Config Updates**
  **Goal:** Add the `channels` key to Matrix configurations.
  **Files:**
  - Modify: `src/iacecil/config.py`
  - Modify: `docs/instance.example/bots/default.py`
  **Approach:** Add `'channels': [],` to the `matrix` dict.
  **Test scenarios:**
  - Happy path: Matrix configuration loads with an empty `channels` list by default.

- U2. **Matrix Connector `is_authorized`**
  **Goal:** Filter incoming Matrix messages based on authorized channels.
  **Files:**
  - Modify: `src/iacecil/connectors/matrix.py`
  - Test: `tests/test_matrix.py`
  **Approach:**
  - Implement `is_authorized(self, envelope) -> bool` on `MatrixConnector`.
  - Fetch the room using `self.client.rooms.get(envelope.conversation_ref)`.
  - Return `True` if `len(room.users) <= 2` (DM).
  - Otherwise, return `True` if `envelope.conversation_ref` is in `self.config.get('channels')`.
  - Return `False` otherwise.
  **Test scenarios:**
  - Happy path: Message in an authorized room ID is authorized.
  - Edge case: Message in a DM (<= 2 users) is authorized even if not in `channels`.
  - Error path: Message in an unauthorized group room (> 2 users) is not authorized.

## Verification
- Echo plugin will echo messages in authorized Matrix rooms or DMs, and ignore messages in unauthorized Matrix rooms.
