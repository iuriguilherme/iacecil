# ia.cecil - Gemini Project Context

## Project Overview
ia.cecil is a multi-platform chatbot framework written in **Python 3.10**. It evolved from several previous bot projects (Paloma, MateBot) into a modular system capable of running on **Telegram, Discord**, and integrating with specialized hardware like **Furhat Robotics** and AI models like **OpenAI (ChatGPT)** and **Deepseek**.

The project uses a hybrid architecture:
- **MVC (Model-View-Controller)** for the core system.
- **Plugin-based** for adding specific bot functionalities.
- **Quart (Async Flask-like)** for the web/view layer.
- **Aiogram / Python-Telegram-Bot** for bot platform integration.
- **ZODB** for object-oriented persistence.

## Project Structure
- `src/iacecil/`: Core application package.
  - `controllers/`: Business logic, platform handlers (Aiogram, Furhat), and persistence (ZODB).
  - `models/`: Data structures.
  - `views/`: Web interface components (Quart app, templates, static files).
- `src/plugins/`: Modular features (e.g., crypto price checks, QR generation, tts, youtube download).
- `instance/`: Local configuration, bot-specific settings, and database storage.
- `doc/`: Documentation, systemd examples, and configuration templates.

## Building and Running

### Prerequisites
- Python 3.10
- `pipenv` (recommended) or `pip`
- System-level `ffmpeg` (for some plugins)

### Installation
Using `pipenv`:
```bash
pipenv install
```
Using `pip`:
```bash
pip install -r requirements.txt
```

### Execution
Run the app in production mode:
```bash
python -m iacecil production
```
Or specifically for Furhat integration:
```bash
python -m iacecil fpersonas
```

### Testing
```bash
pipenv run test
```

## Configuration
The project uses a tiered configuration system:
1. `instance/_bots.py`: Defines the active bot instances.
2. `instance/bots/`: Individual configuration files for each bot (e.g., `testbot.py`).
3. `.env`: Environment variables for Flask/Quart (e.g., `FLASK_APP`, `QUART_APP`).

Bot configuration files typically inherit from `DefaultBotConfig` and define enabled plugins and platform tokens.

## Development Conventions
- **Language**: Core documentation is in **Brazilian Portuguese**, though code symbols are in English.
- **Modularity**: New features should be implemented as independent scripts in `src/plugins/`.
- **Async First**: Many components use `asyncio` (via Aiogram and Quart).
- **Environment Management**: `pipenv` is the preferred tool for dependency and virtualenv management. **Note**: In this sandbox, always use `PIPENV_DONT_LOAD_ENV=1` when running `pipenv` commands to avoid permission errors with the `.env` file.
- **Persistence**: Prefer `ZODB` for persistent object storage.
- **Architecture**: Stick to the MVC pattern in `src/iacecil/` for core changes.

## Key Files
- `src/iacecil/__main__.py`: Entry point for the application.
- `src/iacecil/controllers/_iacecil/production.py`: Core production runner (Quart + Aiogram startup).
- `pyproject.toml` / `Pipfile`: Dependency definitions.
- `instance/_bots.py`: Main bot registry.
- `README.md`: Primary project documentation (in Portuguese).
