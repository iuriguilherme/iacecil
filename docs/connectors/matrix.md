# Matrix Connector Configuration

The Matrix connector allows ia.cecil to interact with Matrix homeservers (like matrix.org).

## Prerequisites

1.  **Homeserver URL**: The URL of your Matrix homeserver (e.g., `https://matrix.org`).
2.  **Access Token**: Preferred for security. You can obtain one from your Matrix client (like Element) or via login.
3.  **User ID / Password**: Alternatively, you can provide a User ID (e.g., `@bot:matrix.org`) and password for bootstrap login.

## Configuration

Add a `matrix` section to your bot configuration file in `instance/bots/<bot_name>.py`.

```python
class MyBotConfig(DefaultBotConfig):
    matrix: dict = {
        'homeserver': 'https://matrix.org',
        'token': 'YOUR_MATRIX_ACCESS_TOKEN',
        # Optional: if using password login instead of token
        # 'user': '@bot:matrix.org',
        # 'password': 'your_password',
        'channels': [
            '!roomid:matrix.org', # Authorized Room ID 1
            '!anotherroom:matrix.org', # Authorized Room ID 2
        ]
    }
```

### Authorization Rules

- **1:1 Direct Messages (DMs)**: The bot always responds to DMs (rooms with 2 or fewer members).
- **Group Rooms**: The bot only responds in rooms listed in the `channels` configuration.
- **Plaintext Only**: Currently, this connector only supports plaintext rooms. Encrypted rooms are detected and ignored with a warning.

## Features

- **Sync Persistence**: The bot saves its sync token to `instance/matrix/` to avoid re-processing old messages on restart.
- **Message Chunking**: Automatically splits messages exceeding 16000 characters (configurable via `MAX_TEXT`).
- **Self-Echo**: The bot filters out its own messages.

## Running

The Matrix connector is compatible with the `connectors_v3` runner.

```bash
python -m iacecil connectors_v3
```
