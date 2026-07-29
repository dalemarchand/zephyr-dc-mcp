# Agent Project Guidelines - Zephyr Scale Data Center MCP Server

This file contains persistent guidelines and rules for AI coding assistants working in this repository.

## 1. Project Overview & Architecture
- **Purpose**: MCP (Model Context Protocol) server for SmartBear Zephyr Scale Data Center (formerly TM4J).
- **Core Server File**: `zephyr_dc_mcp.py` built with `fastmcp` and `httpx`.
- **Standalone Binary**: Compiled via PyInstaller (`./build.sh`) into `dist/zephyr-scale-mcp`.

## 2. Mandatory Environment Configuration
- `ZEPHYR_BASE_URL`: **Mandatory**. Must be specified dynamically (no hardcoded fallback URL allowed).
- `ZEPHYR_PAT`: **Mandatory**. Jira Personal Access Token (`Authorization: Bearer <PAT>`). Fallbacks: `JIRA_PAT`, `ZEPHYR_API_KEY`, `JIRA_API_TOKEN`.
- `ZEPHYR_SSL_VERIFY`: Defaults to OS native certificate store via `truststore`. Set to `false` only to disable verification for testing.

## 3. Versioning & Automated Releases
- **Initial Version**: Started at `0.0.1`.
- **Version File**: The canonical project version is stored in `VERSION` and mirrored in `zephyr_dc_mcp.py` as `__version__`.
- **Version Bump Rules**:
  - **Patch Bump (Default)**: Automatically bumps patch version (e.g. `0.0.1` -> `0.0.2`) on MR merge / commit to `main`.
  - **Minor Bump**: Include `[minor]` or `#minor` in the PR title or commit message (e.g. `0.0.1` -> `0.1.0`).
  - **Major Bump**: Include `[major]` or `#major` in the PR title or commit message (e.g. `0.0.1` -> `1.0.0`).
- **Release Automation**: GitHub Actions ([.github/workflows/release.yml](.github/workflows/release.yml)) automatically bumps the version, builds `dist/zephyr-scale-mcp`, tags `vX.Y.Z`, and creates a GitHub Release with the binary attached.

## 4. Development & Build Guidelines
- **Python Version**: Requires **Python 3.10+**.
- **Dependencies**: Dual support for standard Python (`pip` with `requirements.txt` and `requirements-dev.txt`) and `uv`.
- **PyInstaller Bundling**: Always include `--copy-metadata fastmcp` and `--copy-metadata truststore` when running PyInstaller.
- **OpenCode Integration**: OpenCode uses top-level `"mcp"` key in `opencode.json` with `"type": "local"`, `"command": [...]`, and `"environment": { ... }`.
- **Testing**: All tools must have corresponding unit tests in `tests/test_zephyr_mcp.py` mocking `httpx` calls. Always run `PYTHONPATH=. pytest tests/` before completing tasks.
