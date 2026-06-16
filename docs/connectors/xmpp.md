# XMPP Connector Configuration

The XMPP connector allows ia.cecil to interact with XMPP servers (like Jabber, Conversations.im) for both direct messages and chatrooms (MUC).

## Prerequisites

1.  **JID**: A Jabber ID (e.g., `bot@example.com`).
2.  **Password**: The password for the JID.
3.  **XMPP Server**: A server that supports XEP-0045 (Multi-User Chat) if you plan to use chatrooms.

## Configuration

Add an `xmpp` section to your bot configuration file in `instance/bots/<bot_name>.py`.

```python
class MyBotConfig(DefaultBotConfig):
    xmpp: dict = {
        'jid': 'bot@example.com',
        'password': 'your_password',
        'channels': [
            'room1@conference.example.com', # Authorized MUC JID 1
            'room2@conference.example.com', # Authorized MUC JID 2
        ]
    }
```

### Authorization Rules

- **Direct Messages (chat/normal)**: The bot always responds to DMs.
- **Chatrooms (groupchat)**: The bot only responds in chatrooms listed in the `channels` configuration.
- **Self-Echo**: The bot automatically filters out its own messages in chatrooms to prevent infinite loops.

## Features

- **MUC Support**: Automatically joins configured chatrooms on connection.
- **Message Chunking**: Automatically splits messages exceeding 4000 characters (configurable via `MAX_TEXT`).
- **Authorization**: Mirrors the Discord connector's channel-based authorization logic.

## Running

The XMPP connector is compatible with the `connectors_v3` runner.

```bash
python -m iacecil connectors_v3
```
