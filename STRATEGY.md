---
name: ia.cecil
last_updated: 2026-06-09
---

# ia.cecil Strategy

## Target problem

Writing a chatbot that works across multiple platforms (Telegram, Discord, Furhat) while
adapting its behavior to different communities requires either rewriting from scratch for
each platform or forking the codebase for each community. Both problems are inseparable:
platform abstraction without per-community configuration still forces diverging forks.

## Our approach

Composability via runtime-loadable modules — plugins define capabilities, personalities
define behavior — so any combination of platform, community, and experiment can be
assembled without forking code.

## Who it's for

**Primary:** Developer-researcher running bots for multiple communities — hiring ia.cecil
as a platform to test AI personality and ML concepts without rebuilding infrastructure
each time an experiment starts.

## Key metrics

- **Time-to-new-plugin** — how long to add a new capability from scratch; measures
  whether the plugin system is actually lowering the cost of experimentation (tracked
  informally by commit history)
- **Experiment completion rate** — AI/ML experiments started on the platform that reach
  a working state vs. abandoned mid-build; measures R&D productivity
- **Feature compounding** — how much code becomes permanently reusable across multiple
  bot configurations or experiments; measures whether the composability bet is paying off
  (tracked via plugin reuse across instance/ configs)

## Tracks

### Platform core

Plugin system, personality system, and multi-platform runtime — keeping the framework
extensible and stable as the foundation everything else builds on.

_Why it serves the approach:_ Composability only works if the runtime loading mechanism
is reliable and adding a new module doesn't break existing ones.

### AI/ML integration

Connecting LLMs, local models (Deepseek via Ollama, OpenAI), and personality systems
to the framework as first-class plugins.

_Why it serves the approach:_ AI capabilities are the primary experiment domain; they
need to compose with the same plugin interface as any other feature.

### Community tooling

Plugins that serve real running communities — moderation, fediverse integration,
feedback, welcome flows.

_Why it serves the approach:_ Real deployments are the feedback loop; community tooling
validates that the composability bet works under actual use conditions.
