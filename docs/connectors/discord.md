# Discord Connector Configuration

The Discord connector allows ia.cecil to interact with Discord servers and direct messages.

## Prerequisites

1.  **Discord Bot Token**: Create a bot on the [Discord Developer Portal](https://discord.com/developers/applications).
2.  **Privileged Gateway Intents**: In the Developer Portal, under the **Bot** tab, enable the **Message Content Intent**. This is required for the bot to see message text.
3.  **Invite Bot**: Invite the bot to your server with appropriate permissions (Send Messages, Read Message History, etc.).

## Configuration

Add a `discord` section to your bot configuration file in `instance/bots/<bot_name>.py`.

```python
class MyBotConfig(DefaultBotConfig):
    discord: dict = {
        'token': 'YOUR_DISCORD_BOT_TOKEN',
        'channels': [
            '123456789012345678', # Authorized Channel ID 1
            '876543210987654321', # Authorized Channel ID 2
        ]
    }
```

### Authorization Rules

- **Direct Messages (DMs)**: The bot always responds to DMs.
- **Guild Channels**: The bot only responds in channels listed in the `channels` configuration.
- **Observation**: The bot observes and persists ALL messages it can see (including those in unauthorized channels) to the neutral persistence layer, but it will only trigger plugin handlers (like `echo`) for authorized sources.

## Running

The Discord connector is compatible with the `connectors_v3` runner.

```bash
python -m iacecil connectors_v3
```

Or via Docker, ensuring the `CMD` is set to `connectors_v3`.
