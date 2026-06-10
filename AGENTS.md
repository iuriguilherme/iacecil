# AGENTS.md

This file provides guidance for AI Agents (like Hermes) when working in this repository. It complements CLAUDE.md by focusing on agentic workflows, tool usage, and cross-session state management.

## Agentic Workflow

### Tool Use Policy
- **Verify First:** Always use `read_file` or `search_files` before proposing changes. Never guess file contents.
- **Absolute Paths:** Use absolute paths for all filesystem operations.
- **Non-Interactive:** Use flags like `-y` or `--non-interactive` for CLI tools to prevent hangs.
- **Atomicity:** Prefer `patch` for targeted edits over full file rewrites to minimize regression risk.

### Memory & State
- **Durable Facts:** Save user preferences and environment quirks to persistent memory.
- **Procedural Knowledge:** Save complex, multi-step workflows as skills via `skill_manage`.
- **Session Recall:** Use `session_search` when referencing past work or "last time" discussions.

## Project-Specific Agent Guidance

### Architecture Context
Refer to `CLAUDE.md` for the detailed architectural map of the plugin and personalidade system. 

### Common Tasks for Agents
- **Adding Plugins:** Follow the 3-step process in `CLAUDE.md` (Create file -> Implement `add_handlers` -> Enable in bot config).
- **Adding Personas:** Follow the 4-step process in `CLAUDE.md` (Create module -> Implement functions -> Register in `__init__.py` -> Update bot config).
- **Debugging:** Use `systematic-debugging` skill for root cause analysis before applying fixes.

## Quality Gates
- All new Python code must be compatible with Python 3.10.
- Ensure all new handlers are registered with the dispatcher.
- Verify that configuration changes in `instance/bots/` follow the `BaseSettings` inheritance pattern.
