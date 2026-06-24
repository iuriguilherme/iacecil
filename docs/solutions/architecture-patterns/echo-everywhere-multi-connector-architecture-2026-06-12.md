---
module: iacecil.connectors
date: 2026-06-12
problem_type: architecture_pattern
component: tooling
severity: medium
tags:
  - "multi-connector"
  - "dynamic-loading"
  - "path-sanitization"
  - "logging-recursion"
  - "authorization"
  - "observation-vs-response"
last_refreshed: 2026-06-24
---

# Echo Everywhere: Dynamic Multi-Connector Refactor and Extensibility

## Context
We needed to support multiple chat platforms concurrently (Telegram, XMPP, Discord, Matrix, Loopback) without hardcoding allowlists in the ConnectorManager. We also needed filesystem-safe path sanitization (percent-encoding uppercase letters to avoid HFS+/NTFS case collisions) and a re-entrant guarded log sink handler to prevent operator logs from creating infinite feedback loops.

## Guidance
1. **Dynamic Connector Activation**: Instead of the manager keeping a hardcoded allowlist of connectors, each connector class now defines an `is_active` method or `required_keys`. The manager discovers connectors dynamically at boot.
2. **Filesystem-Safe Paths**: When storing per-connector chat data, all path components are sanitized. Uppercase letters and reserved names are percent-encoded, making the paths safe across case-insensitive filesystems (HFS+, NTFS).
3. **Decoupled Operator Logging**: Internal bot logs can be routed to any platform via `ConnectorLogHandler`. This handler includes a re-entrancy guard to prevent its own delivery failures from re-entering the logger.
4. **Observation is not response**: "Echo everywhere" means every connector *observes* — persists a Neutral Record for every message it can see, on every platform. Whether the bot *replies* is a separate, connector-owned authorization decision (direct messages always; group conversations only when configured). The dispatch core persists the inbound message before consulting authorization, so a suppressed reply never loses the observation. See the `Authorized conversation` entry in `CONCEPTS.md`.

## Why This Matters
This architectural shift removes the bottleneck of updating the core manager whenever a new platform is added. It also ensures cross-platform consistency for persistence and operator logging without breaking the legacy Telegram integration.

## When to Apply
- Adding new chat platform connectors to the bot.
- Designing multi-tenant or multi-platform systems that share a common dispatch core.
- Implementing logging sinks that deliver over the network.
