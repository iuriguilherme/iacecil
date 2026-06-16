# Update Dockerfile Plan

## Problem Frame
The current `Dockerfile` uses outdated syntax and an old method for installing and running the `iacecil` application. It uses `pip install -e .` (editable install, not ideal for a Docker container) and `python3 -m iacecil production` as the command. Furthermore, it refers to `doc/instance/*` which likely doesn't match the actual repository structure (`docs/instance.example/`). 

The goal is to update the Dockerfile to modern syntax, install the application using `pip install .[all]`, and run it using the `iacecil connectors_v3` command.

## Scope Boundaries
- Update `Dockerfile` to use standard, non-editable installation (`pip install .[all]`).
- Update the default `CMD` to `["iacecil", "connectors_v3"]` using the exec form.
- Fix the `cp` command to use the correct `docs/instance.example/` directory instead of `doc/instance/`.
- Ensure standard Docker best practices (like combining RUN commands if appropriate, though simplicity is prioritized).

## Key Technical Decisions
- **Installation method**: Move from `pip install -e .` to `pip install .[all]` to ensure all dependencies, including optional ones for plugins, are installed in the image. Editable mode is an anti-pattern in production images.
- **Entry point / Command**: Use the exec form `CMD ["iacecil", "connectors_v3"]` which is the modern recommended approach for Dockerfiles, preventing signals from being swallowed by a shell wrapper.
- **Directory fix**: Update `cp -r doc/instance/* instance/` to `cp -r docs/instance.example/* instance/` as per the current repository structure.

## Implementation Units

- U1. **Update Dockerfile syntax and commands**

**Goal:** Modernize the Dockerfile and apply the requested execution method.

**Requirements:** R1

**Dependencies:** None

**Files:**
- Modify: `Dockerfile`

**Approach:**
- Change `RUN python3 -m pip install -e .` to `RUN pip install --no-cache-dir .[all]` (using `--no-cache-dir` is a Docker best practice).
- Change `RUN mkdir instance` and `RUN cp -r doc/instance/* instance/` to use `docs/instance.example/`.
- Change `CMD python3 -m iacecil production` to `CMD ["iacecil", "connectors_v3"]`.

**Verification:**
- The Dockerfile can be built successfully using `docker build -t iacecil .`.

## System-Wide Impact
- **Operational Notes**: Container deployments will now default to the `connectors_v3` runner instead of `production`, which aligns with the newer architecture of the application.

## Risks & Dependencies
| Risk | Mitigation |
|------|------------|
| `docs/instance.example/` might not contain everything needed to run `connectors_v3` out of the box without configuration. | This was already an issue with the previous setup; users are expected to mount their own `instance/` volume in production. Copying the example is just for default scaffolding. |
